from rest_framework import serializers
from .models import Commande, ProduitCommande, Produit, FactureTravaux


class ProduitCommandeSerializer(serializers.ModelSerializer):
    nom_produit = serializers.ReadOnlyField(source="produit.nom_produit")

    class Meta:
        model = ProduitCommande
        fields = [
            "id",
            "produit",
            "nom_produit",
            "quantite",
            "prix_unitaire",
            "remise_pourcentage",
            "prix_total",
        ]
        read_only_fields = ["prix_total"]


class CommandeListSerializer(serializers.ModelSerializer):
    nom_client = serializers.ReadOnlyField(source="client.nom_client")

    class Meta:
        model = Commande
        fields = [
            "id",
            "numero_commande",
            "client",
            "nom_client",
            "date_commande",
            "date_livraison_prevue",
            "date_livraison_reelle",
            "statut",
            "montant_ht",
            "montant_tva",
            "montant_ttc",
        ]
        read_only_fields = ["montant_ht", "montant_tva", "montant_ttc"]


class CommandeDetailSerializer(serializers.ModelSerializer):
    produit_commande = ProduitCommandeSerializer(many=True, read_only=True)
    nom_client = serializers.ReadOnlyField(source="client.nom_client")
    devis_numero = serializers.ReadOnlyField(source="devis.numero_devis")
    facture_numero = serializers.ReadOnlyField(source="facture.numero_facture")
    produits_details = serializers.SerializerMethodField()

    class Meta:
        model = Commande
        fields = [
            "id",
            "numero_commande",
            "client",
            "nom_client",
            "devis",
            "devis_numero",
            "produits",
            "produit_commande",
            "produits_details",
            "date_commande",
            "date_livraison_prevue",
            "date_livraison_reelle",
            "statut",
            "tax_rate",
            "montant_ht",
            "montant_tva",
            "montant_ttc",
            "facture",
            "facture_numero",
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
            "date_creation",
            "derniere_mise_a_jour",
            "facture",
        ]

    def get_produits_details(self, obj):
        """Get details about products without creating a through record"""
        produits = Produit.objects.all()
        return [
            {
                "id": p.id,
                "nom_produit": p.nom_produit,
                "prix": p.prix,
                "type_matiere": p.type_matiere,
            }
            for p in produits
        ]

    def to_representation(self, instance):
        """Override to customize the representation of the commande"""
        ret = super().to_representation(instance)
        # Remove produits_details from output unless it's a GET request
        request = self.context.get("request")
        if request and request.method != "GET":
            ret.pop("produits_details", None)
        return ret


class CommandeProduitSerializer(serializers.Serializer):
    """Serializer to add products to a commande"""

    produit = serializers.PrimaryKeyRelatedField(queryset=Produit.objects.all())
    quantite = serializers.IntegerField(min_value=1)
    prix_unitaire = serializers.FloatField(required=False, allow_null=True)
    remise_pourcentage = serializers.FloatField(default=0, min_value=0, max_value=100)


class CommandeGenerateInvoiceSerializer(serializers.Serializer):
    """Serializer to validate generating an invoice from an order"""

    confirmation = serializers.BooleanField(required=True)
