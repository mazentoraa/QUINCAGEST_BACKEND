from rest_framework import generics, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.filters import SearchFilter, OrderingFilter
from django.shortcuts import get_object_or_404

from .models import BonRetour, Client, Matiere
from .bon_retour_serializers import (
    BonRetourSerializer,
    BonRetourListSerializer,
    MatiereForRetourSerializer,
)


class BonRetourViewSet(ModelViewSet):
    """ViewSet for BonRetour with full CRUD operations"""

    queryset = BonRetour.objects.select_related("client").prefetch_related(
        "matiere_retours__matiere"
    )
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["numero_bon", "client__nom_client", "notes"]
    ordering_fields = ["date_retour", "date_reception", "numero_bon"]
    ordering = ["-date_retour"]

    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == "list":
            return BonRetourListSerializer
        return BonRetourSerializer

    def get_queryset(self):
        """Filter queryset based on query parameters"""
        queryset = super().get_queryset()

        # Manual filtering since we don't have django-filter
        status_filter = self.request.query_params.get("status", None)
        client_filter = self.request.query_params.get("client", None)
        date_retour_filter = self.request.query_params.get("date_retour", None)
        date_reception_filter = self.request.query_params.get("date_reception", None)

        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if client_filter:
            queryset = queryset.filter(client_id=client_filter)
        if date_retour_filter:
            queryset = queryset.filter(date_retour=date_retour_filter)
        if date_reception_filter:
            queryset = queryset.filter(date_reception=date_reception_filter)

        return queryset

    def perform_create(self, serializer):
        """Handle creation with custom logic"""
        serializer.save()

    def perform_update(self, serializer):
        """Handle update with custom logic"""
        serializer.save()


@api_view(["GET"])
def client_available_materials(request, client_id):
    """Get all materials available for return for a specific client"""
    try:
        client = get_object_or_404(Client, id=client_id)

        # Get materials with remaining quantity > 0
        materials = client.matieres.filter(remaining_quantity__gt=0)

        response_data = {
            "client": {
                "id": client.id,
                "nom_client": client.nom_client,
                "numero_fiscal": client.numero_fiscal,
            },
            "available_materials": MatiereForRetourSerializer(
                materials, many=True
            ).data,
        }

        return Response(response_data, status=status.HTTP_200_OK)

    except Client.DoesNotExist:
        return Response({"error": "Client not found"}, status=status.HTTP_404_NOT_FOUND)


@api_view(["POST"])
def validate_return_quantities(request):
    """Validate return quantities before creating BonRetour"""
    materials_data = request.data.get("materials", [])

    if not materials_data:
        return Response(
            {"error": "No materials provided for validation"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    validation_results = []
    has_errors = False

    for material_data in materials_data:
        matiere_id = material_data.get("matiere_id")
        quantite_retournee = material_data.get("quantite_retournee", 0)

        try:
            matiere = Matiere.objects.get(id=matiere_id)

            result = {
                "matiere_id": matiere_id,
                "matiere_name": f"{matiere.type_matiere} - {matiere.client.nom_client}",
                "requested_quantity": quantite_retournee,
                "available_quantity": matiere.remaining_quantity,
                "is_valid": quantite_retournee <= matiere.remaining_quantity,
            }

            if not result["is_valid"]:
                result["error"] = (
                    f"Cannot return {quantite_retournee} units. Only {matiere.remaining_quantity} available."
                )
                has_errors = True

            validation_results.append(result)

        except Matiere.DoesNotExist:
            validation_results.append(
                {
                    "matiere_id": matiere_id,
                    "error": "Material not found",
                    "is_valid": False,
                }
            )
            has_errors = True

    return Response(
        {"is_valid": not has_errors, "validation_results": validation_results},
        status=status.HTTP_200_OK,
    )


class BonRetourByClientView(generics.ListAPIView):
    """Get all BonRetour for a specific client"""

    serializer_class = BonRetourListSerializer
    filter_backends = [OrderingFilter]
    ordering_fields = ["date_retour", "date_reception", "numero_bon"]
    ordering = ["-date_retour"]

    def get_queryset(self):
        client_id = self.kwargs["client_id"]
        return BonRetour.objects.filter(client_id=client_id).select_related("client")


class BonRetourStatsView(generics.RetrieveAPIView):
    """Get statistics for BonRetour"""

    def get(self, request, *args, **kwargs):
        # Overall statistics
        total_bons = BonRetour.objects.count()
        draft_bons = BonRetour.objects.filter(status="draft").count()
        sent_bons = BonRetour.objects.filter(status="sent").count()
        completed_bons = BonRetour.objects.filter(status="completed").count()
        cancelled_bons = BonRetour.objects.filter(status="cancelled").count()

        return Response(
            {
                "total_bons_retour": total_bons,
                "status_breakdown": {
                    "draft": draft_bons,
                    "sent": sent_bons,
                    "completed": completed_bons,
                    "cancelled": cancelled_bons,
                },
            },
            status=status.HTTP_200_OK,
        )
