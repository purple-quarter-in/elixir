from rest_framework import status, viewsets
from rest_framework.exceptions import PermissionDenied

from elixir.changelog import changelog

from .utils import custom_success_response


class ModelViewSet(viewsets.ModelViewSet):
    _instance = None
    response_serializer = None
    user_permissions = {
        "get": [],
        "post": [],
        "patch": [],
    }
    changelog = None

    def perform_create(self, serializer, **kwargs):
        self._instance = serializer.save(**kwargs)

    def list(self, request, *args, **kwargs):
        print(
            not request.user.is_superuser,
            len(self.user_permissions["get"]),
            (request.user).has_perms(tuple(self.user_permissions["get"])),
            self.user_permissions["get"],
        )
        if (
            (not request.user.is_superuser)
            and len(self.user_permissions["get"]) > 0
            and not (request.user).has_perms(tuple(self.user_permissions["get"]))
        ):
            raise PermissionDenied()
        queryset = self.filter_queryset(self.get_queryset())
        if request.GET:
            _filter = {key: request.GET[key] for key in request.GET if key != "page"}

            # for key in request.GET:
            #     _filter[key]=request.GET[key]
            queryset = queryset.filter(**(_filter))

        serializer = self.get_serializer(queryset, many=True, context={"request": request})
        return custom_success_response(serializer.data)

    def create(self, request, *args, **kwargs):
        if (
            (not request.user.is_superuser)
            and len(self.user_permissions["post"]) > 0
            and not request.user.has_perms(tuple(self.user_permissions["get"]))
        ):
            raise PermissionDenied()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return custom_success_response(
            self.get_serializer(self._instance).data,
            status=status.HTTP_201_CREATED,
            headers=headers,
        )

    def perform_update(self, serializer):
        self._instance = serializer.save()

    def update(self, request, *args, **kwargs):
        if (
            (not request.user.is_superuser)
            and len(self.user_permissions["patch"]) > 0
            and not request.user.has_perms(tuple(self.user_permissions["get"]))
        ):
            raise PermissionDenied()
        partial = kwargs.pop("partial", True)
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=partial, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        if self.changelog and ("update" in self.changelog):
            changelog(
                self.changelog,
                instance,
                serializer._validated_data,
                "update",
                request.user.id,
            )
        self.perform_update(serializer)
        if getattr(instance, "_prefetched_objects_cache", None):
            instance._prefetched_objects_cache = {}
        return custom_success_response(
            self.response_serializer(self._instance).data
            if self.response_serializer
            else self.get_serializer(self._instance).data,
            message="success, object updated",
        )

    def retrieve(self, request, *args, **kwargs):
        if (
            (not request.user.is_superuser)
            and len(self.user_permissions["get"]) > 0
            and not request.user.has_perms(tuple(self.user_permissions["get"]))
        ):
            raise PermissionDenied()
        instance = self.get_object()
        serializer = self.get_serializer(instance, context={"request": request})
        return custom_success_response(serializer.data)

    def perform_destroy(self, instance):
        instance.delete()

    def destroy(self, request, *args, **kwargs):
        if (
            (not request.user.is_superuser)
            and len(self.user_permissions["get"]) > 0
            and not request.user.has_perms(tuple(self.user_permissions["get"]))
        ):
            raise PermissionDenied()
        instance = self.get_object()
        self.perform_destroy(instance)
        return custom_success_response(
            {}, message="success, object deleted", status=status.HTTP_204_NO_CONTENT
        )


# class CustomPaginationViewset(LimitOffsetPagination):
#     default_limit = settings.DEFAULT_LIMIT

#     def get_paginated_response(self, data):
#         kwargs = {
#             "count": self.count,
#             "next": self.get_next_link(),
#             "previous": self.get_previous_link(),
#         }
#         return custom_success_response(
#             data, message="success", status=status.HTTP_200_OK, **kwargs
#         )
