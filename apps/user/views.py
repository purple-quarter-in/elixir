# Create your views here.
import email

from django.contrib.auth.hashers import make_password
from django.core.mail import send_mail
from django.dispatch import receiver
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes, force_str
from django.utils.html import strip_tags
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from requests import get
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from apps.django_rest_passwordreset.signals import reset_password_token_created
from elixir.rest_permissions import CreateOnly, IsPublisherTeam, IsPublisherTeamOrOwner
from elixir.utils import custom_success_response, set_crated_by_updated_by
from elixir.viewsets import ModelViewSet

# from forms import UserForm
from .models import *
from .serializer import (
    CreateUserSerializer,
    CustomAuthTokenSerializer,
    GetTeamSerializer,
    GetUserSerializer,
    TeamSerializer,
)
from .tokens import account_activation_token


class CustomPasswordResetView:
    @receiver(reset_password_token_created)
    def password_reset_token_created(sender, reset_password_token, *args, **kwargs):
        """
        Handles password reset tokens
        When a token is created, an e-mail needs to be sent to the user
        """
        # send an e-mail to the user
        context = {
            "current_user": reset_password_token.user,
            "username": reset_password_token.user.username,
            "email": reset_password_token.user.email,
            "full_name": reset_password_token.user.get_full_name(),
            "reset_password_url": "{}password-reset/{}".format(
                "www.elixir.purplequarter.co/", reset_password_token.key
            ),
            "site_name": "Elixir",
            "site_domain": "www.elixir.purplequarter.com",
        }
        # render email text
        email_html_message = render_to_string("email/user_reset_password.html", {"data": context})
        email_plaintext_message = strip_tags(email_html_message)
        result = send_mail(
            "Password Reset for {}".format("Elixir."),
            email_plaintext_message,
            "info@purplequarter.com",
            [reset_password_token.user.email],
            html_message=email_html_message,
        )
        return Response(context)


class UserViewSet(ModelViewSet):
    queryset = User.objects.all()
    serializer_class = CreateUserSerializer
    permission_classes = [IsAuthenticated]
    user_permissions = {}

    def get_permissions(self):
        if self.action in ["verify_token", "gauth", "set_password"]:
            return []
        else:
            return super().get_permissions()

    def __init__(self, **kwarg) -> None:
        self.user_permissions["get"] = ["user.view_user"]
        self.user_permissions["post"] = ["user.add_user"]
        self.user_permissions["patch"] = ["user.change_user"]

    def get_serializer_class(self):
        return (
            CreateUserSerializer if self.request.method in ["POST", "PATCH"] else GetUserSerializer
        )

    def retrieve(self, request, pk):
        instance = User.objects.get(_id=pk)
        self.check_object_permissions(request, instance)
        serializer = GetUserSerializer(instance)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        if not request.user.has_perms(self.user_permissions["post"]):
            raise PermissionDenied()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save(is_active=False, **set_crated_by_updated_by(request.user))
        token, created = Token.objects.get_or_create(user=user)
        headers = self.get_success_headers(serializer.data)
        user.profile.user_set.add(user)
        message = render_to_string(
            "email/acc_active_email.html",
            {
                "user": user,
                "uid": urlsafe_base64_encode(force_bytes(user.username)),
                "token": account_activation_token.make_token(user),
            },
        )
        email = send_mail(
            "Activate Your Account",
            message,
            "info@purplequarter.com",
            [user.email],
            html_message=message,
            fail_silently=True,
        )
        return custom_success_response(
            serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers,
            token=token.key,
        )

    def update(self, request, *args, **kwargs):
        if not (
            request.user.has_perms(self.user_permissions["patch"])
            or request.user.id == int(kwargs["pk"])
        ):
            raise PermissionDenied()
        partial = kwargs.pop("partial", True)
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=partial, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        if "profile" in serializer.validated_data:
            instance.groups.clear()
            serializer.validated_data["profile"].user_set.add(instance)
        serializer.save(updated_by=request.user)
        if getattr(instance, "_prefetched_objects_cache", None):
            instance._prefetched_objects_cache = {}
        return custom_success_response(
            self.get_serializer(instance).data, message="success, object updated"
        )

    @action(detail=False, methods=["post"])
    def gauth(self, request):
        dto = request.data
        if "email" not in dto:
            raise ValidationError({"email": ["this field is required."]})
        if not User.objects.filter(
            email=dto["email"], is_active=True, is_email_verified=True
        ).exists():
            raise ValidationError({"message": ["User Doesn't Exist / is not verified."]})
        user = User.objects.get(email=dto["email"])
        user.gauth = dto
        user.save()
        return custom_success_response(
            GetUserSerializer(user).data, token=Token.objects.get_or_create(user=user)[0].key
        )
        pass

    @action(
        detail=False,
        methods=["get"],
        permission_classes=[
            IsAuthenticated,
        ],
    )
    def my_account(self, request):
        return custom_success_response(self.get_serializer(request.user).data)

    @action(detail=False, methods=["post"], permission_classes=AllowAny)
    def verify_token(self, request):
        try:
            uid = force_str(urlsafe_base64_decode(request.data.get("uid")))
            user = User.objects.get(username=uid)
            print(user)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None
        if (
            user is not None
            and account_activation_token.check_token(user, request.data.get("token"))
            # and UserVerificationToken.objects.filter(
            #     token=request.data.get("token"), is_used=False
            # ).exists()
        ):
            user.is_email_verified = True
            user.save()
            return custom_success_response({"message": "Activation link is valid!."})
        else:
            raise ValidationError({"message": ["Activation link is invalid!"]})

    @action(detail=False, methods=["post"])
    def resend_verification_email(self, request):
        if not request.user.has_perms(self.user_permissions["post"]):
            raise PermissionDenied()
        email = request.data.get("email", None)
        if email:
            try:
                user = User.objects.get(email=email)
                if user and user.is_active == False:
                    token = account_activation_token.make_token(user)
                    message = render_to_string(
                        "email/acc_active_email.html",
                        {
                            "user": user,
                            "uid": urlsafe_base64_encode(force_bytes(user.username)),
                            "token": token,
                        },
                    )
                    context = {
                        "user": user,
                        "uid": urlsafe_base64_encode(force_bytes(user.username)),
                        "token": token,
                    }
                    email = send_mail(
                        "Activate Your Account",
                        message,
                        "info@purplequarter.com",
                        [user.email],
                        html_message=message,
                        fail_silently=True,
                    )
                    print(context)
                else:
                    raise ValidationError({"message": ["User Already verified"]})
            except User.DoesNotExist:
                raise ValidationError({"message": ["User Doesnt Exists"]})
        else:
            raise ValidationError({"email": ["This Field is required"]})
        return custom_success_response({"message": "Email sent successfully"})

    @action(detail=False, methods=["post"])
    def set_password(self, request):
        try:
            uid = force_str(urlsafe_base64_decode(request.data.get("uid")))
            user = User.objects.get(username=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None
        if user is not None and user.is_email_verified:
            user.password = make_password(request.data.get("password"))
            user.is_active = True
            user.save()
            # token = UserVerificationToken.objects.get(token=request.data.get("token"))
            # token.is_used = True
            # token.save()
            return custom_success_response({"message": "Password is successfully changed"})
        else:
            raise ValidationError({"message": ["Uid doesnt belong to any user"]})

    @action(detail=False, methods=["patch"])
    def bulk_active(self, request):
        if "users" not in request.data:
            raise ValidationError({"users": ["List of user id is required"]})
        if "active" not in request.data:
            raise ValidationError({"active": ["This boolean field is required"]})

        user = (
            User.objects.all()
            .filter(id__in=request.data.get("users"))
            .update(is_active=request.data.get("active"))
        )
        if user > 0:
            return custom_success_response(
                {
                    "message": [
                        f"{user} user(s) has been marked active = {request.data.get('active')}"
                    ]
                }
            )
        else:
            raise ValidationError({"message": ["Technical error"]})

    @action(detail=True, methods=["patch"])
    def update_password(self, request, pk):
        if not request.user.id == int(pk):
            raise PermissionDenied()
        required_fields = ["old_password", "new_password"]
        for x in required_fields:
            if not request.data.get(x, None) and not request.data.get(x) == "":
                raise ValidationError({x: "This field is required"})
        user = request.user
        if not user.check_password(request.data.get("old_password")):
            raise ValidationError({"message": ["Old Password is Wrong"]})
        user.set_password(request.data.get("new_password"))
        user.save()
        return custom_success_response(
            {"message": "password changes successfully"}, status=status.HTTP_200_OK
        )


class Login(ObtainAuthToken):
    """User Sing-in process
    required field: username['email'], password
    """

    def post(self, request, *args, **kwargs):
        serializer = CustomAuthTokenSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        token, created = Token.objects.get_or_create(user=user)
        _res = {
            "token": token.key,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "profile": {"id": user.profile.id, "name": user.profile.name},
            "function": user.function,
            "timezone": user.time_zone if user.time_zone else None,
        }
        return custom_success_response(
            _res,
            message="User successfully loggedin !",
            status=status.HTTP_200_OK,
            headers={"Location": "/"},
            cookies=_res,
        )


class TeamViewSet(ModelViewSet):
    queryset = Team.objects.all()
    serializer_class = TeamSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method in ["POST", "PATCH"]:
            return TeamSerializer
        else:
            return GetTeamSerializer

    def perform_create(self, serializer, **kwargs):
        if Team.objects.filter(name=serializer.validated_data["name"]).exists():
            raise ValidationError(
                {"message": [f"Team with name {serializer.validated_data['name']} already exists"]}
            )
        self._instance = serializer.save(**set_crated_by_updated_by(self.request.user))
