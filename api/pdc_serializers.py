from rest_framework import serializers
from .models import Cd, PdC, Produit, FactureProduits


class PdCSerializer(serializers.ModelSerializer):
    nom_produit = serializers.ReadOnlyField(source="produit.nom_produit")
    ref_produit = serializers.ReadOnlyField(source="produit.ref_produit")
    class Meta:
        model = PdC
        fields = '__all__'
        read_only_fields = ["prix_total"]


class CdListSerializer(serializers.ModelSerializer):
    nom_client = serializers.ReadOnlyField(source="client.nom_client")
    devis = serializers.ReadOnlyField(source="devis.numero_devis")
    code_client = serializers.ReadOnlyField(source="client.code_client")

    class Meta:
        model = Cd
        fields = [
            "id",
            "devis",
            "numero_commande",
            "client",
            "nom_client",
            "code_client",
            "date_commande",
            "date_livraison_prevue",
            "date_livraison_reelle",
            "statut",
            "timbre_fiscal",
            "mode_paiement",
            "montant_ht",
            "montant_tva",
            "montant_ttc",
        ]
        read_only_fields = ["montant_ht", "montant_tva", "montant_ttc", "numero_commande"]


class CDetailSerializer(serializers.ModelSerializer):
    produit_commande = PdCSerializer(many=True, read_only=True)
    nom_client = serializers.ReadOnlyField(source="client.nom_client")
    devis_numero = serializers.ReadOnlyField(source="devis.numero_devis")
    facture_numero = serializers.ReadOnlyField(source="facture.numero_facture")
    code_client = serializers.ReadOnlyField(source="client.code_client")
    bons = serializers.PrimaryKeyRelatedField(
        many=True, queryset=FactureProduits.objects.all(), required=False
    )

    class Meta:
        model = Cd
        fields = [
            "id",
            "nature",
            "numero_commande",
            "client",
            "nom_client",
            "code_client",
            "devis",
            "devis_numero",
            "produits",
            "produit_commande",
            "date_commande",
            "date_livraison_prevue",
            "date_livraison_reelle",
            "statut",
            "mode_paiement",
            "mixte_comptant",
            "tax_rate",
            "montant_ht",
            "montant_tva",
            "timbre_fiscal",
            "montant_ttc",
            "facture",
            "facture_numero",
            "type_facture",
            "bons",
            "notes",
            "conditions_paiement",
            "date_creation",
            "derniere_mise_a_jour",
        ]
        read_only_fields = [
            "montant_ht",
            "montant_tva",
            "montant_ttc",
            "produit_commande",
            "numero_commande",
            "date_creation",
            "derniere_mise_a_jour",
            "facture",
        ]


class CdPSerializer(serializers.Serializer):
    """Serializer to add products to a commande"""

    produit = serializers.PrimaryKeyRelatedField(queryset=Produit.objects.all())
    quantite = serializers.IntegerField(min_value=1)
    prix_unitaire = serializers.FloatField(required=False, allow_null=True)
    remise_pourcentage = serializers.FloatField(default=0, min_value=0, max_value=100)
    bon_id = serializers.PrimaryKeyRelatedField(queryset=FactureProduits.objects.all(), required=False, allow_null=True)
    bon_numero = serializers.CharField(required=False, allow_blank=True, allow_null=True)

class CdGenerateInvoiceSerializer(serializers.Serializer):
    """Serializer to validate generating an invoice from an order"""

    confirmation = serializers.BooleanField(required=True)
