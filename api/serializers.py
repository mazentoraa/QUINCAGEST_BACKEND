from rest_framework import serializers
from .models import Client, Traveaux, Produit, Matiere


class MatiereSerializer(serializers.ModelSerializer):
    client_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Matiere
        fields = (
            "id",
            "nom",
            "description",
            "prix",
            "client_id",
            "date_creation",
            "derniere_mise_a_jour",
        )
        read_only_fields = ("date_creation", "derniere_mise_a_jour")


class ProduitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Produit
        fields = "__all__"
        read_only_fields = ("date_creation", "derniere_mise_a_jour")


class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = "__all__"
        read_only_fields = ("date_creation", "derniere_mise_a_jour")


class TraveauxSerializer(serializers.ModelSerializer):
    client_id = serializers.IntegerField(write_only=True)
    produit_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Traveaux
        fields = (
            "id",
            "client_id",
            "produit_id",
            "duree",
            "quantite",
            "description",
            "date_creation",
            "derniere_mise_a_jour",
        )
        read_only_fields = ("date_creation", "derniere_mise_a_jour")
        extra_kwargs = {
            'duree': {'required': True},
            'quantite': {'required': True}
        }

    def create(self, validated_data):
        client_id = validated_data.pop("client_id")
        produit_id = validated_data.pop("produit_id")
        try:
            client = Client.objects.get(pk=client_id)
            produit = Produit.objects.get(pk=produit_id)
            validated_data["client"] = client
            validated_data["produit"] = produit
        except (Client.DoesNotExist, Produit.DoesNotExist):
            raise serializers.ValidationError("Client or Product not found")

        return super().create(validated_data)
