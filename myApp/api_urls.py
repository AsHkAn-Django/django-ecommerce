from . import api_views
from rest_framework.routers import SimpleRouter, DefaultRouter


router = DefaultRouter()
router.register(r'books', api_views.BookViewset)

urlpatterns = router.urls