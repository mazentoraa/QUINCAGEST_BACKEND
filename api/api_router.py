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
    EntrepriseViewSet,
)
from .invoice_views import FactureTravauxViewSet
from .installments_views import PlanTraiteViewSet, TraiteViewSet
from .facture_matiere_views import FactureMatiereViewSet
from .bon_retour_views import (
    BonRetourViewSet,
    client_available_materials,
    validate_return_quantities,
    BonRetourByClientView,
    BonRetourStatsView,
)
from .devis_views import DevisViewSet
from .commande_views import CommandeViewSet
from .cd_views import CdViewSet
from .facture_views import CommandeProduitViewSet,LineCommandeViewSet,FactureViewSet,PaymentComptantViewSet

from . import dashboard_views


router = DefaultRouter()
router.register(r"clients", ClientViewSet)
router.register(r"traveaux", TraveauxViewSet)
router.register(r"matieres", MatiereViewSet)
router.register(r"produits", ProduitViewSet)
router.register(r"factures", FactureTravauxViewSet)
router.register(r"plans-traite", PlanTraiteViewSet)
router.register(r"traites", TraiteViewSet)
router.register(r"entreprises", EntrepriseViewSet)
router.register(r"factures-matieres", FactureMatiereViewSet)
router.register(r"bons-retour", BonRetourViewSet)
router.register(r"devis", DevisViewSet)
router.register(r"commandes", CommandeViewSet)
router.register(r"commandes-produits", CommandeProduitViewSet)
router.register(r"lignes-commandes", LineCommandeViewSet)
router.register(r"factures_produits", FactureViewSet)
router.register(r"payments-comptants", PaymentComptantViewSet)
router.register(r"cds", CdViewSet)

urlpatterns = [
    path("api/", include(router.urls)),
    path("api/auth/login/", AdminLoginView.as_view(), name="admin-login"),
    path("api/auth/logout/", LogoutView.as_view(), name="logout"),
    path("api/auth/check/", CheckAuthView.as_view(), name="check-auth"),
    # BonRetour specific endpoints
    path(
        "api/clients/<int:client_id>/available-materials/",
        client_available_materials,
        name="client-available-materials",
    ),
    path(
        "api/bons-retour/validate-quantities/",
        validate_return_quantities,
        name="validate-return-quantities",
    ),
    path(
        "api/clients/<int:client_id>/bons-retour/",
        BonRetourByClientView.as_view(),
        name="client-bons-retour",
    ),
    path(
        "api/bons-retour/stats/", BonRetourStatsView.as_view(), name="bons-retour-stats"
    ),
    path(
        "api/dashboard/counts/", dashboard_views.global_counts, name="dashboard-counts"
    ),
    path(
        "api/dashboard/financial-summary/",
        dashboard_views.financial_summary,
        name="dashboard-financial-summary",
    ),
    path(
        "api/dashboard/devis-status/",
        dashboard_views.devis_status_counts,
        name="dashboard-devis-status",
    ),
    path(
        "api/dashboard/commande-status/",
        dashboard_views.commande_status_counts,
        name="dashboard-commande-status",
    ),
    path(
        "api/dashboard/recent-commandes/",
        dashboard_views.recent_commandes,
        name="dashboard-recent-commandes",
    ),
    path(
        "api/dashboard/recent-factures/",
        dashboard_views.recent_factures,
        name="dashboard-recent-factures",
    ),
    path(
        "api/dashboard/main-insights/",
        dashboard_views.main_dashboard_insights,
        name="dashboard-main-insights",
    ),
]

app_name = "api"
