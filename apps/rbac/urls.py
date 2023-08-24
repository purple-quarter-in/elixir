from rest_framework.routers import DefaultRouter

from .views import *

router = DefaultRouter()
router.register("rbac/category-access", AccessCategoryViewset)
router.register("rbac/profile", GroupViewset)
urlpatterns = []
