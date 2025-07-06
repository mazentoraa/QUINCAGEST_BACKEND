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
    prix_unitaire = serializers.FloatField(read_only=True)
    total = serializers.FloatField(read_only=True)


class InvoiceItemSerializer(serializers.Serializer):
    """Serializer for individual work items in an invoice"""
    id = serializers.IntegerField()
    
    # Product details (assumes `produit` is related field on Traveaux)
    produit_id = serializers.IntegerField(source="produit.id", read_only=True)
    code_produit = serializers.CharField(source="produit.code_produit", read_only=True)
    nom_produit = serializers.CharField(source="produit.nom_produit", read_only=True)
    description_produit = serializers.CharField(source="produit.description", read_only=True)
    
    description = serializers.CharField(allow_blank=True, required=False)

    remise_produit = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    remise_percent_produit = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)

    billable = serializers.SerializerMethodField()
    matiere_usages = MatiereUsageInvoiceSerializer(many=True, required=False)

    def get_billable(self, obj):
        quantite = obj.quantite
        prix_unitaire = float(obj.produit.prix or 0)
        remise_percent = float(obj.remise_percent_produit or 0)

        total_ht = quantite * prix_unitaire
        total_remise = total_ht * remise_percent / 100
        total_after_remise = total_ht - total_remise

        return {
            "quantite": quantite,
            "prix_unitaire": prix_unitaire,
            "remise_percent": remise_percent,
            "total_ht_brut": round(total_ht, 2),
            "total_remise": round(total_remise, 2),
            "total_ht": round(total_after_remise, 2),
        }

class FactureTravauxSerializer(serializers.ModelSerializer):
    """Serializer for the invoice model"""

    client_details = serializers.SerializerMethodField()
    items = serializers.SerializerMethodField()
    total_ht = serializers.FloatField(source="montant_ht", read_only=True)
    total_tax = serializers.FloatField(source="montant_tva", read_only=True)
    total_ttc = serializers.FloatField(source="montant_ttc", read_only=True)
    tax_rate = serializers.IntegerField(required=True)
    client = serializers.PrimaryKeyRelatedField(
        queryset=Client.objects.all(),
        write_only=True,  # Retained for writing client ID
    )
    # This field is intended to receive the new price for a specific product.
    prix_unitaire_produit = serializers.FloatField(
        write_only=True, required=False, allow_null=True
    )
    # This field is to identify which product's price to update.
    produit_id = serializers.IntegerField(
        write_only=True, required=False, allow_null=True
    )

    class Meta:
        model = FactureTravaux
        fields = (
            "id",
            "nature", # Facture ou avoir
            "numero_facture",
            "client",  # Add client field to write data
            "client_details",
            "items",
            "produit_id",  # Added for write operations to identify product
            "prix_unitaire_produit",  # Made writable for updating product price
            "date_emission",
            "date_echeance",
            "date_generated",
            "tax_rate",
            "timbre_fiscal",
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
            "code_client":obj.client.code_client,
        }

    
    def get_items(self, obj):
        """Get work items included in the invoice using InvoiceItemSerializer"""
        travaux_qs = obj.travaux.all().select_related("produit").prefetch_related("matiere_usages__matiere")
        return InvoiceItemSerializer(travaux_qs, many=True).data


    @transaction.atomic
    def create(self, validated_data):
        prix_unitaire_produit_val = validated_data.pop("prix_unitaire_produit", None)
        produit_id_val = validated_data.pop("produit_id", None)

        # Also check for price updates in line_items context
        line_items = self.context.get("line_items", [])
        if not line_items:
            raise serializers.ValidationError(
                {"line_items": "At least one line item is required."}
            )

        # Extract product price updates from line_items if not provided in validated_data
        for item in line_items:
            item_produit_id = item.get("produit_id")
            item_prix_unitaire = item.get("prix_unitaire_produit")

            if item_produit_id and item_prix_unitaire:
                try:
                    produit_to_update = Produit.objects.get(id=item_produit_id)
                    produit_to_update.prix = item_prix_unitaire
                    produit_to_update.save(update_fields=["prix"])
                except Produit.DoesNotExist:
                    raise serializers.ValidationError(
                        {
                            "produit": f"Produit with ID {item_produit_id} does not exist."
                        }
                    )

        # Update product price if both values are provided in validated_data
        if produit_id_val is not None and prix_unitaire_produit_val is not None:
            try:
                produit_to_update = Produit.objects.get(id=produit_id_val)
                produit_to_update.prix = prix_unitaire_produit_val
                produit_to_update.save(update_fields=["prix"])
            except Produit.DoesNotExist:
                raise serializers.ValidationError(
                    {"produit": "Produit with this ID does not exist."}
                )

        client = validated_data.get("client")
        if not client:
            raise serializers.ValidationError({"client": "Client is required."})

        travaux_ids = []
        for item in line_items:
            work_id = item.get("work_id")
            if work_id is None:
                raise serializers.ValidationError(
                    {"line_items": "Each line item must have a 'work_id'."}
                )
            travaux_ids.append(work_id)
            travaux = Traveaux.objects.get(id=work_id)
            travaux.remise_produit = item.get("remise_produit", 0)
            travaux.remise_percent_produit = item.get("remise_percent_produit", 0)
            travaux.save()

        unique_travaux_ids = list(set(travaux_ids))

        # Use select_related to get fresh product data including updated prices
        travaux_list = Traveaux.objects.select_related("produit").filter(
            id__in=unique_travaux_ids, client=client
        )

        if len(travaux_list) != len(unique_travaux_ids):
            found_ids = {t.id for t in travaux_list}
            missing_or_mismatched_ids = [
                tid for tid in unique_travaux_ids if tid not in found_ids
            ]
            raise serializers.ValidationError(
                {
                    "line_items": f"Some work items not found, do not belong to this client, or were duplicated. Problematic work_ids: {missing_or_mismatched_ids}"
                }
            )

        tax_rate = validated_data.get("tax_rate")
        if tax_rate is None:
            raise serializers.ValidationError({"tax_rate": "Tax rate is required."})

        timbre_fiscal = validated_data.pop("timbre_fiscal", None)

        numero_facture = validated_data.get("numero_facture")
        if not numero_facture:
            today = timezone.now().strftime("%Y%m%d")
            count = FactureTravaux.objects.filter(
                numero_facture__startswith=f"INV-{today}"
            ).count()
            numero_facture = f"INV-{today}-{count + 1:03d}"

        # Create invoice instance without totals initially
        invoice_create_data = {
            "client": client,
            "date_emission": validated_data.get("date_emission", timezone.now().date()),
            "date_echeance": validated_data.get("date_echeance"),
            "statut": validated_data.get("statut", "draft"),
            "numero_facture": numero_facture,
            "tax_rate": tax_rate,
            "timbre_fiscal": timbre_fiscal,
            "notes": validated_data.get("notes"),
            "conditions_paiement": validated_data.get("conditions_paiement"),
        }
        # Remove None values to avoid overriding model defaults if not provided
        invoice_create_data = {
            k: v for k, v in invoice_create_data.items() if v is not None
        }
        invoice = FactureTravaux(**invoice_create_data)
        invoice.save()
    
        invoice.travaux.set(travaux_list)

        # Now call calculate_totals with fresh data (the model method now uses select_related)
        invoice.calculate_totals()
        invoice.save(
            update_fields=[
                "montant_ht",
                "montant_tva",
                "montant_ttc",
                "derniere_mise_a_jour",
            ]
        )

        return invoice


class FactureTravauxDetailSerializer(FactureTravauxSerializer):
    """Detailed serializer with additional fields for invoice retrieval"""

    client_name = serializers.CharField(source="client.nom_client", read_only=True)
    code_client= serializers.CharField(source="client.code_client", read_only=True)
    class Meta(FactureTravauxSerializer.Meta):
        fields = FactureTravauxSerializer.Meta.fields + ("client_name","code_client")
