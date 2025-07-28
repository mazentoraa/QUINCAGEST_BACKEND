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
    
    #Tresorerie
    KPIView,
    ScheduleView,
    TraiteView,
    PeriodView
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
from .matiere_purchase_views import MatierePurchaseViewSet
from .devis_views import DevisViewSet
from .commande_views import CommandeViewSet
from .cd_views import CdViewSet
from .facture_views import CommandeProduitViewSet,LineCommandeViewSet,FactureViewSet,PaymentComptantViewSet

from . import dashboard_views
from .views import MatierePremiereAchatViewSet
from .views import FactureAchatMatiereViewSet
from .views import BonLivraisonMatiereViewSet
from .views import FournisseurViewSet
from .views import ConsommableViewSet
from .views import (
    BonRetourFournisseurViewSet,
    fournisseur_available_materials,
    validate_return_quantities_fournisseur,
    BonRetourFournisseurByFournisseurView,
    BonRetourFournisseurStatsView,
)

from .views import PlanTraiteFournisseurViewSet, TraiteFournisseurViewSet
from .views import EmployeViewSet
from .views import AvanceViewSet,FichePaieViewSet
from .views import AvoirViewSet
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
router.register(r"commandes", CommandeViewSet, basename="commandes")

router.register(r"commandes-produits", CommandeProduitViewSet)
router.register(r"lignes-commandes", LineCommandeViewSet)
router.register(r"factures_produits", FactureViewSet)
router.register(r"payments-comptants", PaymentComptantViewSet)
router.register(r"cds", CdViewSet)
router.register(r"matiere-purchase", MatierePurchaseViewSet)
router.register(r'matiere-achat', MatierePremiereAchatViewSet, basename='matiere-achat')
router.register(r"factures-achat-matieres", FactureAchatMatiereViewSet, basename="facture-achat-matiere")
router.register(r'bon-livraison-matieres', BonLivraisonMatiereViewSet, basename='bonlivraisonmatiere')
router.register(r'fournisseurs', FournisseurViewSet, basename='fournisseur')
router.register(r'consommables', ConsommableViewSet)
router.register(r"bons-retour-fournisseurs", BonRetourFournisseurViewSet, basename="bon-retour-fournisseur")
router.register(r"plans-traite-fournisseur", PlanTraiteFournisseurViewSet, basename="plan-traite-fournisseur")
router.register(r"traites-fournisseur", TraiteFournisseurViewSet, basename="traite-fournisseur")
router.register(r'employes', EmployeViewSet)
router.register(r'avances', AvanceViewSet, basename='avance')
router.register(r'fiches-paie', FichePaieViewSet)

router.register(r'avoirs', AvoirViewSet)
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
    # BonRetourFournisseur specific endpoints
    path(
        "api/fournisseurs/<int:fournisseur_id>/available-materials/",
        fournisseur_available_materials,
        name="fournisseur-available-materials",
    ),
    path(
        "api/bons-retour-fournisseurs/validate-quantities/",
        validate_return_quantities_fournisseur,
        name="validate-return-quantities-fournisseur",
    ),
    path(
        "api/fournisseurs/<int:fournisseur_id>/bons-retour-fournisseurs/",
        BonRetourFournisseurByFournisseurView.as_view(),
        name="fournisseur-bons-retour",
    ),
    path(
        "api/bons-retour-fournisseurs/stats/",
        BonRetourFournisseurStatsView.as_view(),
        name="bons-retour-fournisseur-stats",
    ),
    path("api/kpis/", KPIView.as_view()),
    path("api/schedule/", ScheduleView.as_view(), name="schedule"),
    path("api/tresorerietraites/", TraiteView.as_view(), name="traites"),
    path('api/period/', PeriodView.as_view(), name="period"),
]

app_name = "api"