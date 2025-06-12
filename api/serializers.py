from rest_framework import serializers
from .models import Client, Traveaux, Produit, Matiere, MatiereUsage, Entreprise
from drf_extra_fields.fields import Base64ImageField
from django.db import transaction


class MatiereSerializer(serializers.ModelSerializer):
    client_id = serializers.PrimaryKeyRelatedField(
        queryset=Client.objects.all(), source="client"
    )
    client_name = serializers.CharField(source="client.nom_client", read_only=True)
    prix_unitaire = serializers.FloatField(required=False)

    class Meta:
        model = Matiere
        fields = (
            "id",
            "numero_bon",
            "type_matiere",
            "reception_date",
            "client_name",
            "client_id",
            "description",
            "prix_unitaire",
            "date_creation",
            "quantite",
            "remaining_quantity",
            "derniere_mise_a_jour",
            "width",
            "length",
            "thickness",
            "surface",
        )
        extra_kwargs = {
            "type_matiere": {"required": True},
            "description": {"required": False},
            "prix_unitaire": {"required": False},
            "client_id": {"required": True},
            "numero_bon": {"required": False, "allow_null": True, "allow_blank": True},
            "quantite": {"required": True},
        }
        read_only_fields = (
            "date_creation",
            "derniere_mise_a_jour",
            "remaining_quantity",
        )


class ProduitSerializer(serializers.ModelSerializer):
    # Optional: Use Base64ImageField for easier image uploads via API
    image = Base64ImageField(required=False)

    class Meta:
        model = Produit
        fields = [
            "id",
            "nom_produit",
            "description",
            "type_matiere",
            "prix",
            "image",
            "epaisseur",
            "longueur",
            "largeur",
            "surface",
            "date_creation",
            "derniere_mise_a_jour",
            "code_produit",
        ]


class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = "__all__"
        read_only_fields = ("date_creation", "derniere_mise_a_jour")

        def validate_numero_fiscal(self, value):
            import re
            pattern = r'^\d{3}\s\d{4}[A-Z]/[A-Z]/[A-Z]/\d{3}$'
            if not re.match(pattern, value):
                raise serializers.ValidationError(
                    "Format invalide. Format attendu : 000 0000X/X/X/000"
                )
            return value


class MatiereUsageSerializer(serializers.ModelSerializer):
    matiere_id = serializers.IntegerField()

    class Meta:
        model = MatiereUsage
        fields = ("matiere_id", "quantite_utilisee")


class TraveauxSerializer(serializers.ModelSerializer):
    client_id = serializers.IntegerField()
    produit_id = serializers.IntegerField()
    client_name = serializers.CharField(source="client.nom_client", read_only=True)
    produit_name = serializers.CharField(source="produit.nom_produit", read_only=True)
    matiere_usages = MatiereUsageSerializer(many=True, required=False)

    class Meta:
        model = Traveaux
        fields = (
            "id",
            "client_id",
            "produit_id",
            "client_name",
            "produit_name",
            "duree",
            "quantite",
            "description",
            "date_creation",
            "matiere_usages",
            "derniere_mise_a_jour",
        )
        read_only_fields = (
            "date_creation",
            "derniere_mise_a_jour",
            "client_name",
            "produit_name",
        )
        extra_kwargs = {"duree": {"required": True}, "quantite": {"required": True}}

    @transaction.atomic
    def create(self, validated_data):
        client_id = validated_data.pop("client_id")
        produit_id = validated_data.pop("produit_id")
        matiere_usages_data = validated_data.pop("matiere_usages", [])

        try:
            client = Client.objects.get(pk=client_id)
            produit = Produit.objects.get(pk=produit_id)
            validated_data["client"] = client
            validated_data["produit"] = produit
        except (Client.DoesNotExist, Produit.DoesNotExist):
            raise serializers.ValidationError("Client or Product not found")

        travaux = Traveaux.objects.create(**validated_data)

        # Process material usage
        for matiere_usage_data in matiere_usages_data:
            matiere_id = matiere_usage_data.get("matiere_id")
            quantite_utilisee = matiere_usage_data.get("quantite_utilisee")

            try:
                matiere = Matiere.objects.get(pk=matiere_id)

                # Check if we have enough quantity
                if matiere.remaining_quantity < quantite_utilisee:
                    raise serializers.ValidationError(
                        f"Not enough material available. Only {matiere.remaining_quantity} units of {matiere.type_matiere} remaining."
                    )

                # Create the usage record
                MatiereUsage.objects.create(
                    travaux=travaux,
                    matiere=matiere,
                    quantite_utilisee=quantite_utilisee,
                )

                # Update the remaining quantity
                matiere.remaining_quantity -= quantite_utilisee
                matiere.save()

            except Matiere.DoesNotExist:
                raise serializers.ValidationError(
                    f"Material with ID {matiere_id} not found"
                )

        return travaux

    def update(self, instance, validated_data):
        if "matiere_usages" in validated_data:
            matiere_usages_data = validated_data.pop("matiere_usages")

            # Reset quantities for existing usages first
            for usage in instance.matiere_usages.all():
                matiere = usage.matiere
                matiere.remaining_quantity += usage.quantite_utilisee
                matiere.save()
                usage.delete()

            # Add new usages
            for matiere_usage_data in matiere_usages_data:
                matiere_id = matiere_usage_data.get("matiere_id")
                quantite_utilisee = matiere_usage_data.get("quantite_utilisee")
                try:
                    matiere = Matiere.objects.get(pk=matiere_id)

                    # Check if we have enough quantity
                    if matiere.remaining_quantity < quantite_utilisee:
                        raise serializers.ValidationError(
                            f"Not enough material available. Only {matiere.remaining_quantity} units of {matiere.type_matiere} remaining."
                        )

                    # Create the usage record
                    MatiereUsage.objects.create(
                        travaux=instance,
                        matiere=matiere,
                        quantite_utilisee=quantite_utilisee,
                    )

                    # Update the remaining quantity
                    matiere.remaining_quantity -= quantite_utilisee
                    matiere.save()

                except Matiere.DoesNotExist:
                    raise serializers.ValidationError(
                        f"Material with ID {matiere_id} not found"
                    )

        return super().update(instance, validated_data)


class EntrepriseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Entreprise
        fields = "__all__"
