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

        # Try to get product ID from different sources
        produit_id = (
            request.data.get("produit")
            or request.data.get("produit_id")
            or request.query_params.get("produit")
            or request.query_params.get("produit_id")
        )

        if not produit_id:
            return Response(
                {"error": "Product ID required in request data or query params"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            with transaction.atomic():
                # Debug: Check what products exist in this commande
                existing_products = PdC.objects.filter(cd=commande)
                existing_product_details = [
                    {
                        "pdc_id": p.id,
                        "produit_id": p.produit_id,
                        "produit_name": p.produit.nom_produit,
                        "quantite": p.quantite,
                    }
                    for p in existing_products
                ]
                print(f"Commande {commande.id} details:")
                print(f"  - Numero: {commande.numero_commande}")
                print(f"  - Client: {commande.client.nom_client}")
                print(f"  - Existing products: {existing_product_details}")
                print(
                    f"  - Looking for product ID: {produit_id} (type: {type(produit_id)})"
                )

                # Convert produit_id to int if it's a string
                try:
                    produit_id = int(produit_id)
                except (ValueError, TypeError):
                    return Response(
                        {"error": f"Invalid product ID format: {produit_id}"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                produit_commande = PdC.objects.get(cd=commande, produit_id=produit_id)
                print(
                    f"Found PdC record: {produit_commande.id} for product {produit_commande.produit.nom_produit}"
                )

                produit_commande.delete()
                print(
                    f"Successfully deleted product {produit_id} from commande {commande.id}"
                )

                # Recalculate commande totals
                commande.calculate_totals()
                commande.save()

                # Return updated commande data
                return Response(
                    CDetailSerializer(commande, context={"request": request}).data,
                    status=status.HTTP_200_OK,
                )
        except PdC.DoesNotExist:
            # More detailed error message
            existing_product_ids = list(
                PdC.objects.filter(cd=commande).values_list("produit_id", flat=True)
            )
            return Response(
                {
                    "error": f"Product with ID {produit_id} not found in the order",
                    "existing_products": existing_product_ids,
                    "commande_id": commande.id,
                    "commande_numero": commande.numero_commande,
                    "debug_info": existing_product_details,
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            print(f"Unexpected error in remove_product: {str(e)}")
            return Response(
                {"error": f"Unexpected error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
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
