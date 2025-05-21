from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ClientViewSet,
    AdminLoginView,
    LogoutView,
    CheckAuthView,
    TraveauxViewSet,
    MatiereViewSet,
    ProduitViewSet,
    EntrepriseViewSet
)
from .invoice_views import FactureTravauxViewSet
from .installments_views import PlanTraiteViewSet, TraiteViewSet


router = DefaultRouter()
router.register(r"clients", ClientViewSet)
router.register(r"traveaux", TraveauxViewSet)
router.register(r"matieres", MatiereViewSet)
router.register(r"produits", ProduitViewSet)
router.register(r"factures", FactureTravauxViewSet)
router.register(r'plans-traite', PlanTraiteViewSet)
router.register(r'traites', TraiteViewSet)
router.register(r'entreprises', EntrepriseViewSet)


urlpatterns = [
    path("api/", include(router.urls)),
    path("api/auth/login/", AdminLoginView.as_view(), name="admin-login"),
    path("api/auth/logout/", LogoutView.as_view(), name="logout"),
    path("api/auth/check/", CheckAuthView.as_view(), name="check-auth"),
]

app_name = "api"
