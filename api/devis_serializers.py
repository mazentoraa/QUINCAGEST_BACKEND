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
            "timbre_fiscal",  
        ]
        read_only_fields = ["montant_ht", "montant_tva", "montant_ttc"]


class DevisProduitSerializer(serializers.Serializer):
    produit = serializers.PrimaryKeyRelatedField(queryset=Produit.objects.all())
    quantite = serializers.IntegerField(min_value=1)
    prix_unitaire = serializers.FloatField(required=False, allow_null=True)
    remise_pourcentage = serializers.FloatField(default=0, min_value=0, max_value=100)


class DevisDetailSerializer(serializers.ModelSerializer):
    produit_devis = ProduitDevisSerializer(many=True, read_only=True)
    nom_client = serializers.ReadOnlyField(source="client.nom_client")
    produits_details = serializers.SerializerMethodField()
    code_client = serializers.ReadOnlyField(source="client.code_client")
    produits = DevisProduitSerializer(many=True, write_only=True, required=False)

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
            "timbre_fiscal",  
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

    def _group_products(self, produits_data):
        # Regroupe les produits par ID et additionne les quantités
        grouped = {}
        for prod in produits_data:
            pid = prod["produit"].id if hasattr(prod["produit"], "id") else prod["produit"]
            if pid not in grouped:
                grouped[pid] = prod.copy()
            else:
                grouped[pid]["quantite"] += prod["quantite"]
                # Optionnel : écrase prix/remise par le dernier
                grouped[pid]["prix_unitaire"] = prod.get("prix_unitaire", grouped[pid].get("prix_unitaire"))
                grouped[pid]["remise_pourcentage"] = prod.get("remise_pourcentage", grouped[pid].get("remise_pourcentage", 0))
        return list(grouped.values())

    def update(self, instance, validated_data):
        produits_data = validated_data.pop("produits", None)
        # Met à jour les autres champs
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        # Met à jour les produits si fournis
        if produits_data is not None:
            # Supprimer les anciens produits
            instance.produit_devis.all().delete()
            produits_data = self._group_products(produits_data)
            # Ajouter les nouveaux produits
            for prod in produits_data:
                ProduitDevis.objects.create(
                    devis=instance,
                    produit=prod["produit"],
                    quantite=prod["quantite"],
                    prix_unitaire=prod.get("prix_unitaire"),
                    remise_pourcentage=prod.get("remise_pourcentage", 0),
                )
            instance.calculate_totals()
            instance.save()
        return instance

    def create(self, validated_data):
        produits_data = validated_data.pop("produits", None)
        devis = Devis.objects.create(**validated_data)
        if produits_data:
            produits_data = self._group_products(produits_data)
            for prod in produits_data:
                ProduitDevis.objects.create(
                    devis=devis,
                    produit=prod["produit"],
                    quantite=prod["quantite"],
                    prix_unitaire=prod.get("prix_unitaire"),
                    remise_pourcentage=prod.get("remise_pourcentage", 0),
                )
            devis.calculate_totals()
            devis.save()
        return devis


class DevisConvertToCommandeSerializer(serializers.Serializer):
    confirmation = serializers.BooleanField(required=True)
    timbre_fiscal = serializers.DecimalField(required=False, max_digits=10, decimal_places=3)
    notes = serializers.CharField(required=False, allow_blank=True)
