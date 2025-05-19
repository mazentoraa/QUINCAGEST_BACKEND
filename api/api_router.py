from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ClientViewSet, AdminLoginView, LogoutView, CheckAuthView, TraveauxViewSet, MatiereViewSet, ProduitViewSet


router = DefaultRouter()
router.register(r'clients', ClientViewSet)
router.register(r'traveaux', TraveauxViewSet)
router.register(r'matieres', MatiereViewSet)
router.register(r'produits', ProduitViewSet)


urlpatterns = [
    path('api/', include(router.urls)),
    path('api/auth/login/', AdminLoginView.as_view(), name='admin-login'),
    path('api/auth/logout/', LogoutView.as_view(), name='logout'),
    path('api/auth/check/', CheckAuthView.as_view(), name='check-auth'),
]

app_name = 'api'