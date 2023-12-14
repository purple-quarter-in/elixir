from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Q
from rest_framework import status, viewsets
from rest_framework.exceptions import PermissionDenied

from elixir.changelog import changelog

from .utils import custom_success_response


class ModelViewSet(viewsets.ModelViewSet):
    _instance = None
    response_serializer = None
    user_permissions = {"get": [], "post": [], "patch": [], "delete": []}
    changelog = None
    filtering = None
    pagination = False
    sorting = None

    def perform_create(self, serializer, **kwargs):
        self._instance = serializer.save(**kwargs)

    def list(self, request, *args, **kwargs):
        if (
            (not request.user.is_superuser)
            and len(self.user_permissions["get"]) > 0
            and not (request.user).has_perms(tuple(self.user_permissions["get"]))
        ):
            raise PermissionDenied()
        queryset = self.get_queryset()
        total_pages = 0
        page_num = 0
        _filter = {}
        _sorting = []
        if request.GET:
            filter_params = ["page", "limit"] + (self.sorting if self.sorting else [])
            for key in request.GET:
                if key not in filter_params:
                    data = request.GET[key]
                    if self.filtering and key in self.filtering:
                        if self.filtering[key]["operation"] == "in":
                            data = (request.GET[key]).split(",")
                            _filter[key + self.filtering[key]["lookup"]] = data
                        elif self.filtering[key]["operation"] == "search":
                            if self.filtering[key]["query"] == "or":
                                Q_filters = Q()
                                for field in self.filtering[key]["fields"]:
                                    param = f'{field}{self.filtering[key]["lookup"]}'
                                    Q_filters |= Q(**{param: data})
                                queryset = queryset.filter(Q_filters)
                        elif self.filtering[key]["operation"] == "from_to":
                            key_array = key.split("_")
                            data = request.GET[key]
                            _filter[
                                "_".join(key_array[:-1]) + self.filtering[key]["lookup"]
                            ] = data
                        else:
                            _filter[key + self.filtering[key]["lookup"]] = data
                    else:
                        _filter[key] = data
                elif self.sorting and key in self.sorting:
                    _sorting.append(("-" if request.GET[key] == "1" else "") + key)

            # for key in request.GET:
            #     _filter[key]=request.GET[key]

            queryset = queryset.filter(**(_filter))
            print(queryset.query)
            if len(_sorting) > 0:
                for sort_key in _sorting:
                    queryset = queryset.order_by(sort_key)
            if self.pagination:
                limit = request.GET.get("limit", None)
                page_num = request.GET.get("page", 0)
                if page_num is not None:
                    paginator = Paginator(queryset, limit if limit else 10)
                    try:
                        queryset = paginator.page(page_num)
                        total_pages = paginator.num_pages
                    except PageNotAnInteger:
                        queryset = paginator.page(1)
                        page_num = 1
                    except EmptyPage:
                        queryset = paginator.page(paginator.num_pages)
                        page_num = 1
        serializer = self.get_serializer(queryset, many=True, context={"request": request})
        return custom_success_response(
            serializer.data, current_page=page_num, total_pages=total_pages
        )

    def create(self, request, *args, **kwargs):
        if (
            (not request.user.is_superuser)
            and len(self.user_permissions["post"]) > 0
            and not request.user.has_perms(tuple(self.user_permissions["post"]))
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
            and not request.user.has_perms(tuple(self.user_permissions["patch"]))
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
            and len(self.user_permissions["delete"]) > 0
            and not request.user.has_perms(tuple(self.user_permissions["delete"]))
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
