from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from django.db.models import Q, Sum, F, ExpressionWrapper
from django.db import transaction
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import FactureTravaux, Traveaux, Client
from .invoice_serializers import (
    FactureTravauxSerializer,
    FactureTravauxDetailSerializer,
)


class FactureTravauxViewSet(viewsets.ModelViewSet):
    """
    API pour la gestion des factures de travaux.

    Liste toutes les factures, crée de nouvelles factures, et modifie ou supprime les factures existantes.
    """

    permission_classes = [IsAdminUser]
    queryset = FactureTravaux.objects.all().order_by("-date_emission")
    serializer_class = FactureTravauxSerializer

    def get_serializer_class(self):
        if self.action == "retrieve":
            return FactureTravauxDetailSerializer
        return FactureTravauxSerializer

    def get_queryset(self):
        """
        Optional filtering by client, status, or date range
        """
        queryset = self.queryset

        # Filter by client if specified
        client_id = self.request.query_params.get("client_id")
        if client_id:
            queryset = queryset.filter(client_id=client_id)

        # Filter by status if specified
        status = self.request.query_params.get("status")
        if status:
            queryset = queryset.filter(statut=status)

        # Filter by date range if specified
        date_from = self.request.query_params.get("date_from")
        date_to = self.request.query_params.get("date_to")
        if date_from:
            queryset = queryset.filter(date_emission__gte=date_from)
        if date_to:
            queryset = queryset.filter(date_emission__lte=date_to)

        return queryset.prefetch_related(
            "travaux",
            "travaux__produit",
            "travaux__matiere_usages",
            "travaux__matiere_usages__matiere",
        )

    @swagger_auto_schema(
        operation_description="Créer une nouvelle facture",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["client", "line_items", "date_emission", "tax_rate"],
            properties={
                "client": openapi.Schema(
                    type=openapi.TYPE_INTEGER, description="ID of the Client"
                ),
                "line_items": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        required=["work_id"],
                        properties={
                            "work_id": openapi.Schema(
                                type=openapi.TYPE_INTEGER,
                                description="ID of the Traveaux (work item)",
                            ),
                            "produit_id": openapi.Schema(
                                type=openapi.TYPE_INTEGER,
                                description="ID of the product (for reference)",
                            ),
                            "produit_name": openapi.Schema(
                                type=openapi.TYPE_STRING,
                                description="Name of the product (for reference)",
                            ),
                            "description_travail": openapi.Schema(
                                type=openapi.TYPE_STRING,
                                description="Description of the work (for reference)",
                            ),
                            "quantite_produit": openapi.Schema(
                                type=openapi.TYPE_NUMBER,
                                description="Quantity of the product used (for reference)",
                            ),
                            "prix_unitaire_produit": openapi.Schema(
                                type=openapi.TYPE_NUMBER,
                                description="Unit price of product (for reference)",
                            ),
                            "remise_produit": openapi.Schema(
                                type=openapi.TYPE_NUMBER,
                                description="Discount value per product",
                            ),
                            "remise_percent_produit": openapi.Schema(
                                type=openapi.TYPE_NUMBER,
                                description="Discount rate per product",
                            ),
                            "matiere_usages": openapi.Schema(
                                type=openapi.TYPE_ARRAY,
                                items=openapi.Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        "matiere_id": openapi.Schema(
                                            type=openapi.TYPE_INTEGER,
                                            description="ID of the material (for reference)",
                                        ),
                                        "nom_matiere": openapi.Schema(
                                            type=openapi.TYPE_STRING,
                                            description="Name of the material (for reference)",
                                        ),
                                        "type_matiere": openapi.Schema(
                                            type=openapi.TYPE_STRING,
                                            description="Type of the material (for reference)",
                                        ),
                                        "thickness": openapi.Schema(
                                            type=openapi.TYPE_INTEGER,
                                            description="Thickness (for reference)",
                                        ),
                                        "length": openapi.Schema(
                                            type=openapi.TYPE_INTEGER,
                                            description="Length (for reference)",
                                        ),
                                        "width": openapi.Schema(
                                            type=openapi.TYPE_INTEGER,
                                            description="Width (for reference)",
                                        ),
                                        "quantite_utilisee": openapi.Schema(
                                            type=openapi.TYPE_INTEGER,
                                            description="Quantity of material used (for reference)",
                                        ),
                                        "prix_unitaire": openapi.Schema(
                                            type=openapi.TYPE_NUMBER,
                                            description="Unit price of material (for reference)",
                                        ),
                                    },
                                ),
                                description="List of materials used for this work item (for reference)",
                            ),
                        },
                    ),
                    description="List of line items (work items) for the invoice.",
                ),
                "numero_facture": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Invoice number (optional, auto-generated if not provided)",
                ),
                "date_emission": openapi.Schema(
                    type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE
                ),
                "date_echeance": openapi.Schema(
                    type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE, nullable=True
                ),
                "tax_rate": openapi.Schema(type=openapi.TYPE_NUMBER, default=20),
                "timbre_fiscal": openapi.Schema(type=openapi.TYPE_NUMBER, default=1),
                "statut": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    enum=["draft", "sent", "paid", "cancelled"],
                    default="draft",
                ),
                "notes": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    nullable=True,
                    description="Additional notes on the invoice",
                ),
                "conditions_paiement": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    nullable=True,
                    description="Payment terms and conditions",
                ),
            },
        ),
        responses={
            201: FactureTravauxSerializer,
            400: "Données invalides ou incomplètes",
        },
    )
    def create(self, request, *args, **kwargs):
        line_items = request.data.get("line_items", [])

        # Pass request.data directly to the serializer,
        # it will handle 'client' and other fields.
        # Pass 'line_items' via context for the serializer's create method.
        serializer = self.get_serializer(
            data=request.data,
            context={"line_items": line_items, "request": request},
        )

        serializer.is_valid(raise_exception=True)
        invoice = serializer.save()

        return Response(
            self.get_serializer(invoice).data, status=status.HTTP_201_CREATED
        )

    @swagger_auto_schema(
        operation_description="Rechercher des factures",
        manual_parameters=[
            openapi.Parameter(
                "query",
                openapi.IN_QUERY,
                description="Texte à rechercher dans les numéros de facture ou noms de clients",
                type=openapi.TYPE_STRING,
                required=True,
            )
        ],
        responses={
            200: FactureTravauxSerializer(many=True),
            400: "Paramètre de recherche manquant",
        },
    )
    @action(detail=False, methods=["get"])
    def search(self, request):
        """
        Search invoices by invoice number or client name
        """
        query = request.query_params.get("query")
        if not query:
            return Response(
                {"error": "Search query parameter is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        invoices = self.queryset.filter(
            Q(numero_facture__icontains=query) | Q(client__nom_client__icontains=query)
        )

        serializer = self.get_serializer(invoices, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Récupérer les factures par client",
        manual_parameters=[
            openapi.Parameter(
                "client_id",
                openapi.IN_QUERY,
                description="ID du client pour filtrer les factures",
                type=openapi.TYPE_INTEGER,
                required=True,
            )
        ],
        responses={
            200: FactureTravauxSerializer(many=True),
            400: "Paramètre client_id manquant",
        },
    )
    @action(detail=False, methods=["get"])
    def by_client(self, request):
        """
        Get invoices filtered by client
        """
        client_id = request.query_params.get("client_id")
        if not client_id:
            return Response(
                {"error": "client_id parameter is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        invoices = self.queryset.filter(client_id=client_id)
        serializer = self.get_serializer(invoices, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Mettre à jour le statut d'une facture",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["statut"],
            properties={
                "statut": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    enum=["draft", "sent", "paid", "cancelled"],
                )
            },
        ),
        responses={
            200: FactureTravauxSerializer,
            400: "Statut invalide",
            404: "Facture non trouvée",
        },
    )
    @action(detail=True, methods=["patch"])
    def update_status(self, request, pk=None):
        """
        Update the status of an invoice
        """
        try:
            invoice = self.get_object()
            new_status = request.data.get("statut")

            if not new_status or new_status not in dict(FactureTravaux.STATUT_CHOICES):
                return Response(
                    {"error": "Valid status is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            invoice.statut = new_status
            invoice.save()

            serializer = self.get_serializer(invoice)
            return Response(serializer.data)

        except FactureTravaux.DoesNotExist:
            return Response(
                {"error": "Invoice not found"}, status=status.HTTP_404_NOT_FOUND
            )

    @swagger_auto_schema(
        operation_description="Récupérer un résumé des factures",
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "total_invoices": openapi.Schema(type=openapi.TYPE_INTEGER),
                    "total_amount": openapi.Schema(type=openapi.TYPE_NUMBER),
                    "paid_amount": openapi.Schema(type=openapi.TYPE_NUMBER),
                    "pending_amount": openapi.Schema(type=openapi.TYPE_NUMBER),
                    "statut_summary": openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "draft": openapi.Schema(type=openapi.TYPE_INTEGER),
                            "sent": openapi.Schema(type=openapi.TYPE_INTEGER),
                            "paid": openapi.Schema(type=openapi.TYPE_INTEGER),
                            "cancelled": openapi.Schema(type=openapi.TYPE_INTEGER),
                        },
                    ),
                },
            )
        },
    )
    @action(detail=False, methods=["get"])
    def summary(self, request):
        """
        Get summary statistics about invoices
        """
        total_invoices = self.queryset.count()

        # Status counts
        status_counts = {
            status: self.queryset.filter(statut=status).count()
            for status, _ in FactureTravaux.STATUT_CHOICES
        }

        # Calculate total, paid, and pending amounts
        # This assumes we have calculated total fields on the invoice
        # If not, you'd need to calculate them here
        total_amount = 0
        paid_amount = 0
        pending_amount = 0

        # In a real system, you would likely have these as fields on the model
        # But for now, we'll calculate them
        invoices = self.queryset.all()
        for invoice in invoices:
            invoice_total = 0
            for travaux in invoice.travaux.all():
                if travaux.produit.prix:
                    invoice_total += travaux.quantite * travaux.produit.prix

            if invoice.statut == "paid":
                paid_amount += invoice_total
            elif invoice.statut in ["draft", "sent"]:
                pending_amount += invoice_total

            if invoice.statut != "cancelled":
                total_amount += invoice_total

        return Response(
            {
                "total_invoices": total_invoices,
                "total_amount": total_amount,
                "paid_amount": paid_amount,
                "pending_amount": pending_amount,
                "status_summary": status_counts,
            }
        )


