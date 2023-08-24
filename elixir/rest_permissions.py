from rest_framework import permissions
from rest_framework.permissions import SAFE_METHODS

# from profiles.models import UserProfileMap


class IsPublisherTeam(permissions.BasePermission):
    message = "User is not of type publisher"

    def has_permission(self, request, view):
        if request.user.is_authenticated and request.user.user_type == "PUBLISHER_TEAM":
            return True


class IsPublisherTeamOrOwner(permissions.BasePermission):
    message = "Your are not a  publisher or you do not own this object"

    def has_permission(self, request, view):
        return bool(request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        return request.user._id == obj._id or request.user.user_type == "PUBLISHER_TEAM"


class IsAdminOrCreateOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.user and request.user.user_type == "PUBLISHER_TEAM":
            return True
        return request.method.lower() == "post"


class IsSelfOrNotUpdate(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user == obj


class IsAdminOrReferredNotSet(permissions.BasePermission):
    message = "cannot set referred_by when it already exists"

    def has_permission(self, request, view):
        return bool(request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        return (not bool(obj.referred_by)) or request.user.is_staff


class IsOwnerOrReadOnly(permissions.BasePermission):
    message = "you do not own this object"

    def has_object_permission(self, request, view, obj):
        return (
            True
            if request.method in SAFE_METHODS
            else (hasattr(obj, "id") and obj.id == request.user.id)
        )


class CreateOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.method.lower() == "post"
