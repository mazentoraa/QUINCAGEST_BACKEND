from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from django.utils import timezone

from .models import Cd, PdC, Client
from .pdc_serializers import (
    CdListSerializer,
    CDetailSerializer,
    PdCSerializer,
    CdPSerializer,
    CdGenerateInvoiceSerializer,
)


class CdViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing orders (commande)
    """

    queryset = Cd.objects.all().order_by("-date_commande", "-numero_commande")

    def get_serializer_class(self):
        if self.action == "list":
            return CdListSerializer
        return CDetailSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            commande = serializer.save()

            # Handle adding products if provided in the request
            if "produits" in request.data and isinstance(
                request.data["produits"], list
            ):
                for produit_data in request.data["produits"]:
                    produit_serializer = CdPSerializer(data=produit_data)
                    if produit_serializer.is_valid():
                        PdC.objects.create(
                            cd=commande,
                            produit=produit_serializer.validated_data["produit"],
                            quantite=produit_serializer.validated_data["quantite"],
                            prix_unitaire=produit_serializer.validated_data.get(
                                "prix_unitaire"
                            ),
                            remise_pourcentage=produit_serializer.validated_data.get(
                                "remise_pourcentage", 0
                            ),
                        )
                    else:
                        # Log error but continue with other products
                        print(f"Invalid product data: {produit_serializer.errors}")

            # Calculate totals after adding products
            commande.calculate_totals()
            commande.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def add_product(self, request, pk=None):
        commande = self.get_object()
        serializer = CdPSerializer(data=request.data)

        if serializer.is_valid():
            with transaction.atomic():
                # Check if product already exists in commande
                produit = serializer.validated_data["produit"]
                produit_commande, created = PdC.objects.get_or_create(
                    cd=commande,
                    produit=produit,
                    defaults={
                        "quantite": serializer.validated_data["quantite"],
                        "prix_unitaire": serializer.validated_data.get("prix_unitaire"),
                        "remise_pourcentage": serializer.validated_data.get(
                            "remise_pourcentage", 0
                        ),
                    },
                )

                if not created:
                    # Update existing product
                    produit_commande.quantite = serializer.validated_data["quantite"]
                    if "prix_unitaire" in serializer.validated_data:
                        produit_commande.prix_unitaire = serializer.validated_data[
                            "prix_unitaire"
                        ]
                    if "remise_pourcentage" in serializer.validated_data:
                        produit_commande.remise_pourcentage = serializer.validated_data[
                            "remise_pourcentage"
                        ]
                    produit_commande.save()

                # Recalculate commande totals
                commande.calculate_totals()
                commande.save()

                return Response(PdCSerializer(produit_commande).data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["delete"])
    def remove_product(self, request, pk=None):
        commande = self.get_object()
        produit_id = request.data.get("produit")

        if not produit_id:
            return Response(
                {"error": "Product ID required"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            with transaction.atomic():
                produit_commande = PdC.objects.get(
                    cd=commande, produit_id=produit_id
                )
                produit_commande.delete()

                # Recalculate commande totals
                commande.calculate_totals()
                commande.save()

                return Response(status=status.HTTP_204_NO_CONTENT)
        except PdC.DoesNotExist:
            return Response(
                {"error": "Product not found in the order"},
                status=status.HTTP_404_NOT_FOUND,
            )

    @action(detail=True, methods=["post"])
    def generate_invoice(self, request, pk=None):
        commande = self.get_object()

        # Check if commande is in "completed" state
        if commande.statut != "completed":
            return Response(
                {"error": "Only completed orders can generate invoices"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check if invoice already exists
        if commande.facture is not None:
            return Response(
                {"error": "This order already has an invoice"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate request data
        serializer = CdGenerateInvoiceSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Check confirmation
        if not serializer.validated_data.get("confirmation"):
            return Response(
                {"error": "Confirmation is required to generate an invoice"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            with transaction.atomic():
                facture = commande.generate_invoice()

                if facture:
                    from .invoice_serializers import FactureTravauxSerializer

                    return Response(
                        {
                            "success": "Invoice generated successfully",
                            "invoice_id": facture.id,
                        },
                        status=status.HTTP_201_CREATED,
                    )
                else:
                    return Response(
                        {"error": "Failed to generate invoice"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def update_status(self, request, pk=None):
        commande = self.get_object()
        new_status = request.data.get("status")

        if not new_status:
            return Response(
                {"error": "New status is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        valid_statuses = [status_choice[0] for status_choice in Cd.STATUT_CHOICES]
        if new_status not in valid_statuses:
            return Response(
                {
                    "error": f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Special validation for "completed" status
        if new_status == "completed" and not commande.produit_commande.exists():
            return Response(
                {"error": "Cannot mark as completed: order has no products"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        commande.statut = new_status
        commande.save()

        return Response(CDetailSerializer(commande).data)

    @action(detail=False, methods=["get"])
    def by_client(self, request):
        client_id = request.query_params.get("client_id")

        if not client_id:
            return Response(
                {"error": "client_id parameter is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            client = Client.objects.get(pk=client_id)
            commandes = Cd.objects.filter(client=client).order_by("-date_commande")
            serializer = CdListSerializer(commandes, many=True)
            return Response(serializer.data)
        except Client.DoesNotExist:
            return Response(
                {"error": f"Client with ID {client_id} not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
