from rest_framework import serializers
from .models import Client, Traveaux, Produit, Matiere, MatiereUsage, FactureTravaux
from .serializers import ClientSerializer
from django.db import transaction
from django.utils import timezone


class MatiereUsageInvoiceSerializer(serializers.Serializer):
    """Serializer for material usage within an invoice"""

    matiere_id = serializers.IntegerField()
    nom_matiere = serializers.CharField(read_only=True)
    type_matiere = serializers.CharField(read_only=True)
    quantite_utilisee = serializers.FloatField()
    prix_unitaire = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True
    )
    total = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)


class InvoiceItemSerializer(serializers.Serializer):
    """Serializer for individual work items in an invoice"""

    id = serializers.IntegerField()
    produit_name = serializers.CharField(read_only=True)
    description = serializers.CharField(allow_blank=True, required=False)
    billable = serializers.DictField(child=serializers.FloatField())
    matiere_usages = MatiereUsageInvoiceSerializer(many=True, required=False)


class FactureTravauxSerializer(serializers.ModelSerializer):
    """Serializer for the invoice model"""

    client_details = serializers.SerializerMethodField()
    items = serializers.SerializerMethodField()
    total_ht = serializers.DecimalField(
        source="montant_ht", max_digits=10, decimal_places=2, read_only=True
    )
    total_tax = serializers.DecimalField(
        source="montant_tva", max_digits=10, decimal_places=2, read_only=True
    )
    total_ttc = serializers.DecimalField(
        source="montant_ttc", max_digits=10, decimal_places=2, read_only=True
    )
    tax_rate = serializers.DecimalField(max_digits=5, decimal_places=2, required=True)
    client = serializers.PrimaryKeyRelatedField(
        queryset=Client.objects.all(), write_only=True
    )

    class Meta:
        model = FactureTravaux
        fields = (
            "id",
            "numero_facture",
            "client",  # Add client field to write data
            "client_details",
            "items",
            "date_emission",
            "date_echeance",
            "date_generated",
            "tax_rate",
            "total_ht",
            "total_tax",
            "total_ttc",
            "statut",
        )
        read_only_fields = ("date_generated",)

    def get_client_details(self, obj):
        """Get client details for the invoice"""
        return {
            "id": obj.client.id,
            "nom_client": obj.client.nom_client,
            "numero_fiscal": obj.client.numero_fiscal,
            "adresse": obj.client.adresse,
            "telephone": obj.client.telephone,
            "email": obj.client.email,
        }

    def get_items(self, obj):
        """Get work items included in the invoice"""
        items = []
        for travaux in obj.travaux.all():
            item = {
                "id": travaux.id,
                "produit_name": travaux.produit.nom_produit,
                "description": travaux.description or "",
                "billable": {
                    "quantite": travaux.quantite,
                    "prix_unitaire": float(travaux.produit.prix or 0),
                    "total_ht": float(travaux.quantite * (float(travaux.produit.prix) or 0.0)),
                },
                "matiere_usages": [],
            }

            for usage in travaux.matiere_usages.all():
                matiere = usage.matiere
                prix_unitaire = float(matiere.prix_unitaire or 0.0)
                item["matiere_usages"].append(
                    {
                        "matiere_id": matiere.id,
                        "nom_matiere": matiere.type_matiere,
                        "type_matiere": matiere.type_matiere,
                        "quantite_utilisee": usage.quantite_utilisee,
                        "prix_unitaire": prix_unitaire,
                        "total": float(usage.quantite_utilisee * prix_unitaire),
                    }
                )

            items.append(item)

        return items

    @transaction.atomic
    def create(self, validated_data):
        print("Creating invoice with data:", validated_data)
        travaux_ids = self.context.get("travaux_ids", [])
        print("Travaux IDs:", travaux_ids)

        # Get client from validated_data instead of context
        client = validated_data.pop("client", None)
        if not client:
            client_id = self.context.get("client_id")
            print("Client ID from context:", client_id)
            if not client_id:
                raise serializers.ValidationError("Client ID is required")

            try:
                client = Client.objects.get(pk=client_id)
            except Client.DoesNotExist:
                raise serializers.ValidationError(
                    f"Client with ID {client_id} not found"
                )

        if not travaux_ids:
            raise serializers.ValidationError("At least one work item is required")

        travaux_list = Traveaux.objects.filter(id__in=travaux_ids, client=client)
        if len(travaux_list) != len(travaux_ids):
            raise serializers.ValidationError(
                "Some work items not found or do not belong to this client"
            )

        # Calculate totals first
        total_ht = 0
        for travaux in travaux_list:
            prix = travaux.produit.prix or 0
            # Convert to float to ensure consistent type for multiplication
            total_ht += float(travaux.quantite) * float(prix)

        # Get tax rate
        tax_rate = validated_data["tax_rate"]

        # Calculate tax and total amounts
        total_tax = float(total_ht) * (float(tax_rate) / 100)
        total_ttc = total_ht + total_tax

        # Generate a unique invoice number if not provided
        if not validated_data.get("numero_facture"):
            today = timezone.now().strftime("%Y%m%d")
            count = FactureTravaux.objects.filter(
                numero_facture__startswith=f"INV-{today}"
            ).count()
            validated_data["numero_facture"] = f"INV-{today}-{count + 1:03d}"

        # Create and save the invoice with all data at once
        invoice = FactureTravaux(
            client=client,
            date_emission=validated_data.get("date_emission", timezone.now().date()),
            date_echeance=validated_data.get("date_echeance"),
            statut=validated_data.get("statut", "draft"),
            numero_facture=validated_data.get("numero_facture"),
            tax_rate=tax_rate,
            montant_ht=total_ht,
            montant_tva=total_tax,
            montant_ttc=total_ttc,
        )

        # Save first to get an ID before adding many-to-many relationships
        invoice.save()

        # Now that we have a saved instance with an ID, set the many-to-many relationship
        invoice.travaux.set(travaux_list)

        return invoice


class FactureTravauxDetailSerializer(FactureTravauxSerializer):
    """Detailed serializer with additional fields for invoice retrieval"""

    client_name = serializers.CharField(source="client.nom_client", read_only=True)

    class Meta(FactureTravauxSerializer.Meta):
        fields = FactureTravauxSerializer.Meta.fields + ("client_name",)
