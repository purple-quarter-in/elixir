from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser, BaseUserManager, Group
from django.db import models
from django.utils import timezone


# User = get_user_model()
# Create your models here.
class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("Users require an email field")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    mobile = models.CharField(max_length=12)
    email = models.EmailField(unique=True, db_index=True)
    region = models.CharField(max_length=50, blank=True, null=True)
    function = models.CharField(max_length=50)
    time_zone = models.CharField(max_length=50, blank=True, null=True)
    gauth = models.JSONField(default=dict, blank=True, null=True)
    is_email_verified = models.BooleanField(default=0)
    profile = models.ForeignKey(
        Group, on_delete=models.DO_NOTHING, related_name="user_group", null=True
    )
    gender = models.CharField(max_length=30, default=None, null=True)
    reporting_to = models.ForeignKey(
        "user.User",
        on_delete=models.DO_NOTHING,
        default=None,
        null=True,
        blank=True,
        related_name="reporting_user",
    )
    created_by = models.ForeignKey(
        "user.User",
        on_delete=models.DO_NOTHING,
        default=None,
        null=True,
        related_name="created_by_user",
    )
    updated_by = models.ForeignKey(
        "user.User",
        on_delete=models.DO_NOTHING,
        default=None,
        null=True,
        related_name="updated_by_user",
    )
    archived = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    # REQUIRED_FIELDS = ['username']
    REQUIRED_FIELDS = ["first_name", "last_name", "mobile", "function"]

    def get_full_name(self):
        """
        Returns the first_name plus the last_name, with a space in between.
        """
        full_name = "{} {}".format(self.first_name, self.last_name)
        return full_name.strip()
