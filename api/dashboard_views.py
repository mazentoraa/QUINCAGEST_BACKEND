from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Sum, Count

from .models import Client, Produit, FactureProduits, Devis, Commande, Fournisseur, Employe
from .commande_serializers import CommandeListSerializer


@api_view(["GET"])
def global_counts(request):
    """
    Provides total counts for major entities.
    """
    counts = {
        "total_clients": Client.objects.count(),
        "total_produits": Produit.objects.count(),
        "total_devis": Devis.objects.count(),
        "total_commandes": Commande.objects.count(),
        "total_factures_travaux": FactureProduits.objects.count(),
        "total_fournisseurs": Fournisseur.objects.count(),
        "total_employees": Employe.objects.count(),
    }
    return Response(counts)


@api_view(["GET"])
def financial_summary(request):
    """
    Provides a summary of financial data.
    """
    total_invoiced = (
        FactureProduits.objects.aggregate(total=Sum("montant_ttc"))["total"] or 0
    )
    total_paid = (
        FactureProduits.objects.filter(statut="paid").aggregate(
            total=Sum("montant_ttc")
        )["total"]
        or 0
    )

    summary = {
        "total_invoiced_ttc": total_invoiced,
        "total_paid_ttc": total_paid,
    }
    return Response(summary)


@api_view(["GET"])
def devis_status_counts(request):
    """
    Provides counts of Devis (quotes) by status.
    """
    status_counts = (
        Devis.objects.values("statut")
        .annotate(count=Count("statut"))
        .order_by("statut")
    )
    return Response(list(status_counts))


@api_view(["GET"])
def commande_status_counts(request):
    """
    Provides counts of Commandes (orders) by status.
    """
    status_counts = (
        Commande.objects.values("statut")
        .annotate(count=Count("statut"))
        .order_by("statut")
    )
    return Response(list(status_counts))


@api_view(["GET"])
def recent_commandes(request):
    """
    Provides a list of the 5 most recent commandes.
    """
    recent_commandes = Commande.objects.order_by("-date_creation")[:5]

    serializer = CommandeListSerializer(recent_commandes, many=True)
    return Response(serializer.data)


@api_view(["GET"])
def recent_factures(request):
    """
    Provides a list of the 5 most recent factures.
    """
    recent_factures = FactureProduits.objects.order_by("-date_creation")[:5]
    from .invoice_serializers import (
        FactureProduitsSerializer,
    )  # Assuming you have a FactureProduitsSerializer

    serializer = FactureProduitsSerializer(recent_factures, many=True)
    return Response(serializer.data)


# You might want a combined dashboard view
@api_view(["GET"])
def main_dashboard_insights(request):
    """
    Provides a combined set of insights for the main dashboard.
    """
    insights = {
        "counts": {
            "clients": Client.objects.count(),
            "produits": Produit.objects.count(),
            "devis": Devis.objects.count(),
            "commandes": Commande.objects.count(),
            "factures_produits": FactureProduits.objects.count(),
            "fournisseurs": Fournisseur.objects.count(),
            "employees": Employe.objects.count(),
        },
        "financials": {
            "total_invoiced_ttc": FactureProduits.objects.aggregate(
                total=Sum("montant_ttc")
            )["total"]
            or 0,
            "total_paid_ttc": FactureProduits.objects.filter(statut="paid").aggregate(
                total=Sum("montant_ttc")
            )["total"]
            or 0,
        },
        "devis_by_status": list(
            Devis.objects.values("statut")
            .annotate(count=Count("statut"))
            .order_by("statut")
        ),
        "commandes_by_status": list(
            Commande.objects.values("statut")
            .annotate(count=Count("statut"))
            .order_by("statut")
        ),
    }
    return Response(insights)
