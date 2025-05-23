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
    prix_unitaire = serializers.IntegerField(read_only=True)
    total = serializers.IntegerField(read_only=True)


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
    total_ht = serializers.IntegerField(source="montant_ht", read_only=True)
    total_tax = serializers.IntegerField(source="montant_tva", read_only=True)
    total_ttc = serializers.IntegerField(source="montant_ttc", read_only=True)
    tax_rate = serializers.IntegerField(required=True)
    client = serializers.PrimaryKeyRelatedField(
        queryset=Client.objects.all(),
        write_only=True,  # Retained for writing client ID
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
                    "total_ht": float(
                        travaux.quantite * (float(travaux.produit.prix) or 0.0)
                    ),
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
        client = validated_data.get("client")
        if not client:
            raise serializers.ValidationError({"client": "Client is required."})

        line_items = self.context.get("line_items", [])
        if not line_items:
            raise serializers.ValidationError(
                {"line_items": "At least one line item is required."}
            )

        travaux_ids = []
        for item in line_items:
            work_id = item.get("work_id")
            if work_id is None:
                raise serializers.ValidationError(
                    {"line_items": "Each line item must have a 'work_id'."}
                )
            travaux_ids.append(work_id)

        unique_travaux_ids = list(set(travaux_ids))

        travaux_list = Traveaux.objects.filter(id__in=unique_travaux_ids, client=client)

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
            "notes": validated_data.get("notes"),
            "conditions_paiement": validated_data.get("conditions_paiement"),
        }
        # Remove None values to avoid overriding model defaults if not provided
        invoice_create_data = {
            k: v for k, v in invoice_create_data.items() if v is not None
        }

        invoice = FactureTravaux(**invoice_create_data)
        invoice.save()  # Save to get PK

        invoice.travaux.set(travaux_list)  # Set M2M relationship

        # Now call calculate_totals and save again
        invoice.calculate_totals()  # This will set montant_ht, montant_tva, montant_ttc on the instance
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

    class Meta(FactureTravauxSerializer.Meta):
        fields = FactureTravauxSerializer.Meta.fields + ("client_name",)
