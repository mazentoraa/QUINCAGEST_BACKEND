from rest_framework import serializers
from .models import Commande, ProduitCommande, Produit, FactureTravaux


class ProduitCommandeSerializer(serializers.ModelSerializer):
    nom_produit = serializers.ReadOnlyField(source="produit.nom_produit")
    code_produit = serializers.ReadOnlyField(source="produit.code_produit")
    class Meta:
        model = ProduitCommande
        fields = [
            "id",
            "produit",
            "nom_produit",
            "code_produit",
            "quantite",
            "prix_unitaire",
            "remise_pourcentage",
            "prix_total",
        ]
        read_only_fields = ["prix_total"]


class CommandeListSerializer(serializers.ModelSerializer):
    nom_client = serializers.ReadOnlyField(source="client.nom_client")
    devis = serializers.ReadOnlyField(source="devis.numero_devis")
    class Meta:
        model = Commande
        fields = [
            "id",
            "devis",
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
    code_client = serializers.ReadOnlyField(source="client.code_client")
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
            "code_client",
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
            "type_facture",
            "montant_ht",
            "montant_tva",
            "montant_ttc",
            "facture_numero",
            "notes",
            "conditions_paiement",
            "date_creation",
            "derniere_mise_a_jour",
        ]
        read_only_fields = [
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
                "code_produit":p.code_produit ,
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
def create(self, validated_data):
    produits_data = validated_data.pop("produits", [])
    tax_rate = validated_data.get("tax_rate", 0)

    montant_ht = 0
    for produit_data in produits_data:
        q = produit_data["quantite"]
        p = produit_data["prix_unitaire"]
        remise = produit_data.get("remise_pourcentage", 0)
        total = q * p * (1 - remise / 100)
        montant_ht += total

    montant_tva = montant_ht * tax_rate / 100
    montant_ttc = montant_ht + montant_tva

    # ✅ Do not pop montant_ht from validated_data, use the computed one
    commande = Commande.objects.create(
        montant_ht=montant_ht,
        montant_tva=montant_tva,
        montant_ttc=montant_ttc,
        **validated_data
    )

    for produit_data in produits_data:
        ProduitCommande.objects.create(
            commande=commande,
            produit=produit_data["produit"],
            quantite=produit_data["quantite"],
            prix_unitaire=produit_data.get("prix_unitaire"),
            remise_pourcentage=produit_data.get("remise_pourcentage", 0),
            prix_total=(
                produit_data["quantite"]
                * produit_data["prix_unitaire"]
                * (1 - produit_data.get("remise_pourcentage", 0) / 100)
            ),
        )

    return commande


    def update(self, instance, validated_data):
        produits_data = validated_data.pop("produits", [])
        tax_rate = validated_data.get("tax_rate", instance.tax_rate)

        montant_ht = 0
        for produit_data in produits_data:
            q = produit_data["quantite"]
            p = produit_data["prix_unitaire"]
            remise = produit_data.get("remise_pourcentage", 0)
            total = q * p * (1 - remise / 100)
            montant_ht += total

        montant_tva = montant_ht * tax_rate / 100
        montant_ttc = montant_ht + montant_tva

        # Mise à jour des champs principaux
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.montant_ht = montant_ht
        instance.montant_tva = montant_tva
        instance.montant_ttc = montant_ttc
        instance.save()

        # Mise à jour des produits (optionnel)
        # ... (à implémenter si tu le souhaites)

        return instance


class CommandeProduitSerializer(serializers.Serializer):
    """Serializer to add products to a commande"""

    produit = serializers.PrimaryKeyRelatedField(queryset=Produit.objects.all())
    quantite = serializers.IntegerField(min_value=1)
    prix_unitaire = serializers.FloatField(required=False, allow_null=True)
    remise_pourcentage = serializers.FloatField(default=0, min_value=0, max_value=100)


class CommandeGenerateInvoiceSerializer(serializers.Serializer):
    """Serializer to validate generating an invoice from an order"""

    confirmation = serializers.BooleanField(required=True)
