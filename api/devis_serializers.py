from rest_framework import serializers
from .models import Devis, ProduitDevis, Produit, Client


class ProduitDevisSerializer(serializers.ModelSerializer):
    nom_produit = serializers.ReadOnlyField(source="produit.nom_produit")
    code_produit = serializers.ReadOnlyField(source="produit.code_produit")

    class Meta:
        model = ProduitDevis
        fields = [
            "id",
            "produit",
            "nom_produit",
            "quantite",
            "prix_unitaire",
            "remise_pourcentage",
            "prix_total",
            "code_produit",
        ]
        read_only_fields = ["prix_total"]


class DevisListSerializer(serializers.ModelSerializer):
    nom_client = serializers.ReadOnlyField(source="client.nom_client")
    code_client = serializers.ReadOnlyField(source="client.code_client")

    class Meta:
        model = Devis
        fields = [
            "id",
            "code_client",
            "numero_devis",
            "client",
            "nom_client",
            "date_emission",
            "date_validite",
            "statut",
            "montant_ht",
            "montant_tva",
            "montant_ttc",
            "timbre_fiscal",  # ✅ Ajout ici
        ]
        read_only_fields = ["montant_ht", "montant_tva", "montant_ttc"]


class DevisDetailSerializer(serializers.ModelSerializer):
    produit_devis = ProduitDevisSerializer(many=True, read_only=True)
    nom_client = serializers.ReadOnlyField(source="client.nom_client")
    produits_details = serializers.SerializerMethodField()
    code_client = serializers.ReadOnlyField(source="client.code_client")

    class Meta:
        model = Devis
        fields = [
            "id",
            "numero_devis",
            "client",
            "nom_client",
            "code_client",
            "produits",
            "produit_devis",
            "produits_details",
            "date_emission",
            "date_validite",
            "statut",
            "tax_rate",
            "montant_ht",
            "montant_tva",
            "montant_ttc",
            "timbre_fiscal",  # ✅ Ajout ici
            "remarques",
            "notes",
            "conditions_paiement",
            "date_creation",
            "derniere_mise_a_jour",
        ]
        read_only_fields = [
            "montant_ht",
            "montant_tva",
            "montant_ttc",
            "produit_devis",
            "date_creation",
            "derniere_mise_a_jour",
        ]

    def get_produits_details(self, obj):
        produits = Produit.objects.all()
        return [
            {
                "id": p.id,
                "nom_produit": p.nom_produit,
                "prix": p.prix,
                "type_matiere": p.type_matiere,
                "code_produit": p.code_produit,
            }
            for p in produits
        ]

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        request = self.context.get("request")
        if request and request.method != "GET":
            ret.pop("produits_details", None)
        return ret


class DevisProduitSerializer(serializers.Serializer):
    produit = serializers.PrimaryKeyRelatedField(queryset=Produit.objects.all())
    quantite = serializers.IntegerField(min_value=1)
    prix_unitaire = serializers.FloatField(required=False, allow_null=True)
    remise_pourcentage = serializers.FloatField(default=0, min_value=0, max_value=100)


class DevisConvertToCommandeSerializer(serializers.Serializer):
    confirmation = serializers.BooleanField(required=True)
