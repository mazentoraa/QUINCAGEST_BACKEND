from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from django.utils import timezone

from .models import Devis, ProduitDevis, Client
from .devis_serializers import (
    DevisListSerializer,
    DevisDetailSerializer,
    ProduitDevisSerializer,
    DevisProduitSerializer,
    DevisConvertToCommandeSerializer,
)


class DevisViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing quotes (devis)
    """
    queryset = Devis.objects.all()          
    def get_queryset(self):
        if self.action == "deleted":
            return Devis.objects.filter(is_deleted=True).order_by("-date_emission")
        # Pour l'action restore, on veut bien récupérer le devis supprimé aussi
        elif self.action == "restore":
            # Inclure devis supprimés
            return Devis.objects.all()
        else:
            return Devis.objects.filter(is_deleted=False).order_by("-date_emission", "-numero_devis")


    def get_serializer_class(self):
        if self.action == "list":
            return DevisListSerializer
        return DevisDetailSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            # Récupération de la valeur du timbre fiscal si elle est envoyée
            timbre_fiscal = request.data.get("timbre_fiscal", None)
            if timbre_fiscal is not None:
                serializer.validated_data["timbre_fiscal"] = timbre_fiscal

            devis = serializer.save()

            # Ajout des produits si présents
            if "produits" in request.data and isinstance(request.data["produits"], list):
                for produit_data in request.data["produits"]:
                    produit_serializer = DevisProduitSerializer(data=produit_data)
                    if produit_serializer.is_valid():
                        ProduitDevis.objects.create(
                            devis=devis,
                            produit=produit_serializer.validated_data["produit"],
                            quantite=produit_serializer.validated_data["quantite"],
                            prix_unitaire=produit_serializer.validated_data.get("prix_unitaire"),
                            remise_pourcentage=produit_serializer.validated_data.get("remise_pourcentage", 0),
                        )
                    else:
                        print(f"Invalid product data: {produit_serializer.errors}")

            # Calcul des totaux après ajout
            devis.calculate_totals()
            devis.save()

        return Response(self.get_serializer(devis).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def add_product(self, request, pk=None):
        devis = self.get_object()
        serializer = DevisProduitSerializer(data=request.data)

        if serializer.is_valid():
            with transaction.atomic():
                produit = serializer.validated_data["produit"]
                produit_devis, created = ProduitDevis.objects.get_or_create(
                    devis=devis,
                    produit=produit,
                    defaults={
                        "quantite": serializer.validated_data["quantite"],
                        "prix_unitaire": serializer.validated_data.get("prix_unitaire"),
                        "remise_pourcentage": serializer.validated_data.get("remise_pourcentage", 0),
                    },
                )

                if not created:
                    produit_devis.quantite = serializer.validated_data["quantite"]
                    if "prix_unitaire" in serializer.validated_data:
                        produit_devis.prix_unitaire = serializer.validated_data["prix_unitaire"]
                    if "remise_pourcentage" in serializer.validated_data:
                        produit_devis.remise_pourcentage = serializer.validated_data["remise_pourcentage"]
                    produit_devis.save()

                devis.calculate_totals()
                devis.save()

                return Response(ProduitDevisSerializer(produit_devis).data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["delete"])
    def remove_product(self, request, pk=None):
        devis = self.get_object()
        produit_id = request.data.get("produit")

        if not produit_id:
            return Response(
                {"error": "Product ID required"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            with transaction.atomic():
                produit_devis = ProduitDevis.objects.get(
                    devis=devis, produit_id=produit_id
                )
                produit_devis.delete()

                devis.calculate_totals()
                devis.save()

                return Response(status=status.HTTP_204_NO_CONTENT)
        except ProduitDevis.DoesNotExist:
            return Response(
                {"error": "Product not found in the quote"},
                status=status.HTTP_404_NOT_FOUND,
            )

    @action(detail=True, methods=["post"])
    def convert_to_commande(self, request, pk=None):
        devis = self.get_object()

        if devis.statut != "accepted":
            return Response(
                {"error": "Only accepted quotes can be converted to orders"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = DevisConvertToCommandeSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        if not serializer.validated_data.get("confirmation"):
            return Response(
                {"error": "Confirmation is required to convert the quote to an order"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            with transaction.atomic():
                commande = devis.convert_to_commande()
                if commande:
                    from .commande_serializers import CommandeDetailSerializer
                    return Response(
                        CommandeDetailSerializer(commande).data,
                        status=status.HTTP_201_CREATED,
                    )
                else:
                    return Response(
                        {"error": "Failed to convert the quote to an order"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

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
            devis = Devis.objects.filter(client=client).order_by("-date_emission")
            serializer = DevisListSerializer(devis, many=True)
            return Response(serializer.data)
        except Client.DoesNotExist:
            return Response(
                {"error": f"Client with ID {client_id} not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

    def destroy(self, request, *args, **kwargs):
        devis = self.get_object()
        devis.is_deleted = True
        devis.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=["get"])
    def deleted(self, request):
        devis = Devis.objects.filter(is_deleted=True).order_by("-date_emission")
        serializer = DevisListSerializer(devis, many=True)
        return Response(serializer.data)


    @action(detail=True, methods=["post"])
    def restore(self, request, pk=None):
        devis = self.get_object()
        devis.is_deleted = False
        devis.save()
        return Response({"success": "Devis restauré avec succès."}, status=status.HTTP_200_OK)
