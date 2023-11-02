from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import (
    get_password_validators,
    validate_password,
)
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework import exceptions, status
from rest_framework.generics import GenericAPIView

from elixir.utils import custom_success_response

from .models import (
    ResetPasswordToken,
    clear_expired,
    get_password_reset_lookup_field,
    get_password_reset_token_expiry_time,
)
from .serializers import EmailSerializer, PasswordTokenSerializer, ResetTokenSerializer
from .signals import (
    post_password_reset,
    pre_password_reset,
    reset_password_token_created,
)

SITE_URL = settings.SITE_URL
User = get_user_model()

__all__ = [
    "ResetPasswordValidateToken",
    "ResetPasswordConfirm",
    "ResetPasswordRequestToken",
    "reset_password_validate_token",
    "reset_password_confirm",
    "reset_password_request_token",
]

HTTP_USER_AGENT_HEADER = getattr(
    settings, "DJANGO_REST_PASSWORDRESET_HTTP_USER_AGENT_HEADER", "HTTP_USER_AGENT"
)
HTTP_IP_ADDRESS_HEADER = getattr(
    settings, "DJANGO_REST_PASSWORDRESET_IP_ADDRESS_HEADER", "REMOTE_ADDR"
)


class ResetPasswordValidateToken(GenericAPIView):
    """
    An Api View which provides a method to verify that a token is valid
    """

    throttle_classes = ()
    permission_classes = ()
    serializer_class = ResetTokenSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        return custom_success_response({"is_valid": "true"})


class ResetPasswordConfirm(GenericAPIView):
    """
    An Api View which provides a method to reset a password based on a unique token
    """

    throttle_classes = ()
    permission_classes = ()
    serializer_class = PasswordTokenSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        password = serializer.validated_data["password"]
        token = serializer.validated_data["token"]

        # find token
        reset_password_token = ResetPasswordToken.objects.filter(key=token).first()

        # change users password (if we got to this code it means that the user is_active)
        if reset_password_token.user.eligible_for_reset():
            pre_password_reset.send(sender=self.__class__, user=reset_password_token.user)
            try:
                # validate the password against existing validators
                validate_password(
                    password,
                    user=reset_password_token.user,
                    password_validators=get_password_validators(settings.AUTH_PASSWORD_VALIDATORS),
                )
            except ValidationError as e:
                # raise a validation error for the serializer
                raise exceptions.ValidationError({"password": e.messages})

            reset_password_token.user.set_password(password)
            reset_password_token.user.save()
            post_password_reset.send(sender=self.__class__, user=reset_password_token.user)

        # Delete all password reset tokens for this user
        ResetPasswordToken.objects.filter(user=reset_password_token.user).delete()
        return custom_success_response({"detail": "Password has been changed successfully"})


class ResetPasswordRequestToken(GenericAPIView):
    """
    An Api View which provides a method to request a password reset token based on an e-mail address

    Sends a signal reset_password_token_created when a reset token was created
    """

    throttle_classes = ()
    permission_classes = ()
    serializer_class = EmailSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]

        # before we continue, delete all existing expired tokens
        password_reset_token_validation_time = get_password_reset_token_expiry_time()

        # datetime.now minus expiry hours
        now_minus_expiry_time = timezone.now() - timedelta(
            hours=password_reset_token_validation_time
        )

        # delete all tokens where created_at < now - 24 hours
        clear_expired(now_minus_expiry_time)

        # find a user by email address (case insensitive search)
        users = User.objects.filter(
            **{"{}__iexact".format(get_password_reset_lookup_field()): email}
        )

        active_user_found = False

        # iterate over all users and check if there is any user that is active
        # also check whether the password can be changed (is useable), as there could be users that are not allowed
        # to change their password (e.g., LDAP user)
        for user in users:
            if user.eligible_for_reset():
                active_user_found = True
                break

        # No active user found, raise a validation error
        # but not if DJANGO_REST_PASSWORDRESET_NO_INFORMATION_LEAKAGE == True
        if not active_user_found and not getattr(
            settings, "DJANGO_REST_PASSWORDRESET_NO_INFORMATION_LEAKAGE", False
        ):
            raise exceptions.ValidationError(
                {
                    "email": [
                        _(
                            "We couldn't find an account associated with that email, or email is not verified by user."
                        )
                    ],
                }
            )

        # last but not least: iterate over all users that are active and can change their password
        # and create a Reset Password Token and send a signal with the created token
        for user in users:
            if user.eligible_for_reset():
                # define the token as none for now
                token = None

                # check if the user already has a token
                if user.password_reset_tokens.all().count() > 0:
                    # yes, already has a token, re-use this token
                    token = user.password_reset_tokens.all()[0]
                else:
                    # no token exists, generate a new token
                    token = ResetPasswordToken.objects.create(
                        user=user,
                        user_agent=request.META.get(HTTP_USER_AGENT_HEADER, ""),
                        ip_address=request.META.get(HTTP_IP_ADDRESS_HEADER, ""),
                    )
                # send a signal that the password token was created
                # let whoever receives this signal handle sending the email for the password reset
                reset_password_token_created.send(
                    sender=self.__class__, instance=self, reset_password_token=token
                )
                context = {
                    "username": token.user.username,
                    "email": token.user.email,
                    "reset_password_url": "{}password-reset/{}".format(SITE_URL, token.key),
                    "site_name": "Kalagato-DMS",
                    "site_domain": "www.elixir.ai",
                }
        # done
        return custom_success_response(
            {
                "message": "Password reset link sent to your registered mail " + token.user.email,
                **context,
            },
            status=status.HTTP_201_CREATED,
        )


reset_password_validate_token = ResetPasswordValidateToken.as_view()
reset_password_confirm = ResetPasswordConfirm.as_view()
reset_password_request_token = ResetPasswordRequestToken.as_view()
