from rest_framework import serializers
from .models import BonRetour, ProduitRetour, Produit, Client


class ProduitForRetourSerializer(serializers.ModelSerializer):
    """Serializer for products available for return"""

    nom_produit = serializers.CharField()
    quantite_retournee = serializers.IntegerField(min_value=1)

    class Meta:
        model = Produit
        fields = [
            "nom_produit",
            "quantite_retournee",
        ]
        read_only_fields = [
            "id",
            "type_produit",
            "description",
            "thickness",
            "length",
            "width",
            "surface",
            "remaining_quantity",
        ]

    def validate_quantite_retournee(self, value):
        """Validate that return quantity doesn't exceed remaining quantity"""
        if hasattr(self, "instance") and self.instance:
            if value > self.instance.remaining_quantity:
                raise serializers.ValidationError(
                    f"Cannot return {value} units. Only {self.instance.remaining_quantity} remaining."
                )
        return value


class ProduitRetourFreeSerializer(serializers.Serializer):
    nom_produit = serializers.CharField()
    quantite_retournee = serializers.IntegerField(min_value=1)


    class Meta:
        model = ProduitRetour
        fields = ["id", "produit_id", "produit_details", "quantite_retournee"]

    def validate_produit_id(self, value):
        """Validate that the product exists"""
        try:
            produit = Produit.objects.get(id=value)
            return value
        except Produit.DoesNotExist:
            raise serializers.ValidationError("Product not found.")

    def validate(self, attrs):
        """Validate that return quantity doesn't exceed remaining quantity"""
        produit_id = attrs.get("produit_id")
        quantite_retournee = attrs.get("quantite_retournee", 1)

        if produit_id:
            try:
                produit = Produit.objects.get(id=produit_id)
                if quantite_retournee > produit.remaining_quantity:
                    raise serializers.ValidationError(
                        {
                            "quantite_retournee": f"Cannot return {quantite_retournee} units. Only {produit.remaining_quantity} remaining."
                        }
                    )
            except Produit.DoesNotExist:
                raise serializers.ValidationError({"produit_id": "Product not found."})

        return attrs


class ClientBasicSerializer(serializers.ModelSerializer):
    """Basic client serializer for BonRetour"""

    class Meta:
        model = Client
        fields = ["id", "nom_client", "numero_fiscal", "adresse"]


class BonRetourSerializer(serializers.ModelSerializer):
    """Main serializer for BonRetour"""

    client_details = ClientBasicSerializer(source="client", read_only=True)
    produit_retours = ProduitRetourFreeSerializer(many=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = BonRetour
        fields = [
            "id",
            "numero_bon",
            "client",
            "client_details",
            "status",
            "status_display",
            "date_reception",
            "date_retour",
            "date_emission",
            "notes",
            "date_creation",
            "derniere_mise_a_jour",
            "produit_retours",
        ]
        read_only_fields = [
            "id",
            "date_creation",
            "derniere_mise_a_jour",
            "date_emission",
        ]

    def create(self, validated_data):
        produits_data = validated_data.pop("produit_retours", [])
        bon_retour = BonRetour.objects.create(**validated_data)

        for prod_data in produits_data:
            ProduitRetour.objects.create(
                bon_retour=bon_retour,
                nom_produit=prod_data["nom_produit"],
                quantite_retournee=prod_data["quantite_retournee"],
            )
        return bon_retour

    def update(self, instance, validated_data):
        """Update BonRetour and related ProduitRetour instances"""
        produit_retours_data = validated_data.pop("produit_retours", [])

        # Update basic fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Handle produit_retours update
        if produit_retours_data is not None:
            # Clear existing relations
            instance.produit_retours.all().delete()

            # Create new relations
            for produit_retour_data in produit_retours_data:
                ProduitRetour.objects.create(bon_retour=instance, **produit_retour_data)

        return instance


class BonRetourListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing BonRetour"""

    client_name = serializers.CharField(source="client.nom_client", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    total_products = serializers.SerializerMethodField()

    class Meta:
        model = BonRetour
        fields = [
            "id",
            "numero_bon",
            "client_name",
            "status",
            "status_display",
            "date_reception",
            "date_retour",
            "total_products",
        ]

    def get_total_products(self, obj):
        """Get total number of different products in this return"""
        return obj.produit_retours.count()


class ClientMaterialsSerializer(serializers.ModelSerializer):
    """Serializer to show client's available products for return"""

    available_products = serializers.SerializerMethodField()

    class Meta:
        model = Client
        fields = ["id", "nom_client", "numero_fiscal", "available_products"]

    def get_available_products(self, obj):
        """Get all products for this client that have remaining quantity > 0"""
        products = obj.produits.filter(remaining_quantity__gt=0)
        return ProduitForRetourSerializer(products, many=True).data
