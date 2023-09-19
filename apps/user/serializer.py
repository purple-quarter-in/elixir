from django.contrib.auth import authenticate, get_user_model
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from apps.user.models import *

User = get_user_model()
# class CustomTokenSerializer(serializers.Serializer):
#     token = serializers.CharField()
import re

regex = re.compile(r"([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@(kalagato\.)+(co)")


class CustomAuthTokenSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(style={"input_type": "password"})

    def validate(self, data):
        email = data.get("email")
        password = data.get("password")
        if email and password:
            user = authenticate(email=email, password=password)
            if user:
                if not user.is_active:
                    msg = "User account is disabled."
                    raise ValidationError(msg)
            else:
                msg = "User Not Active | Unable to login with given credentials!"
                raise ValidationError(msg)
        else:
            msg = 'Must include "email" and "password".'
            raise ValidationError(msg)

        data["user"] = user
        return data


class GetUserSerializer(serializers.ModelSerializer):
    created_by = serializers.SerializerMethodField()
    reporting_to = serializers.SerializerMethodField()
    profile = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "mobile",
            "first_name",
            "last_name",
            "profile",
            "reporting_to",
            "created_by",
        )

    def get_created_by(self, instance):
        return instance.created_by.get_dict_name_id() if instance.created_by else None

    def get_reporting_to(self, instance):
        return instance.reporting_to.get_dict_name_id() if instance.reporting_to else None

    def get_profile(self, instance):
        return {"id": instance.profile_id, "name": instance.profile.name}


class CreateUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        exclude = ["username"]
        extra_kwargs = {"password": {"write_only": True}}

    # def validate_email(self, data):
    #     if not re.fullmatch(regex, data):
    #         raise ValidationError("Please enter comapany email (@kalagato.co)")
    #     return data

    def create(self, validated_data):
        email = validated_data.pop("email")
        password = validated_data.pop("password")
        username = email
        user = User.objects.create_user(
            email=email, password=password, username=username, **validated_data
        )
        return user


class GetTeamSerializer(serializers.ModelSerializer):
    created_by = serializers.SerializerMethodField()
    updated_by = serializers.SerializerMethodField()
    leader = GetUserSerializer()
    members = GetUserSerializer(read_only=True, many=True)

    class Meta:
        model = Team
        fields = "__all__"
        depth = 1

    def get_created_by(self, instance):
        return instance.created_by.get_full_name()

    def get_updated_by(self, instance):
        return instance.updated_by.get_full_name()


class TeamSerializer(serializers.ModelSerializer):
    created_by = serializers.SerializerMethodField()
    updated_by = serializers.SerializerMethodField()

    class Meta:
        model = Team
        fields = "__all__"

    def get_created_by(self, instance):
        return instance.created_by.get_full_name()

    def get_updated_by(self, instance):
        return instance.updated_by.get_full_name()
