from rest_framework import serializers
from .models import BonRetour, MatiereRetour, Matiere, Client


class MatiereForRetourSerializer(serializers.ModelSerializer):
    """Serializer for materials available for return"""

    remaining_quantity = serializers.IntegerField(read_only=True)
    quantite_retournee = serializers.IntegerField(
        write_only=True, min_value=1, required=False
    )

    class Meta:
        model = Matiere
        fields = [
            "id",
            "type_matiere",
            "description",
            "thickness",
            "length",
            "width",
            "surface",
            "remaining_quantity",
            "quantite_retournee",
        ]
        read_only_fields = [
            "id",
            "type_matiere",
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


class MatiereRetourSerializer(serializers.ModelSerializer):
    """Serializer for MatiereRetour through model"""

    matiere_details = MatiereForRetourSerializer(source="matiere", read_only=True)
    matiere_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = MatiereRetour
        fields = ["id", "matiere_id", "matiere_details", "quantite_retournee"]

    def validate_matiere_id(self, value):
        """Validate that the material exists"""
        try:
            matiere = Matiere.objects.get(id=value)
            return value
        except Matiere.DoesNotExist:
            raise serializers.ValidationError("Material not found.")

    def validate(self, attrs):
        """Validate that return quantity doesn't exceed remaining quantity"""
        matiere_id = attrs.get("matiere_id")
        quantite_retournee = attrs.get("quantite_retournee", 1)

        if matiere_id:
            try:
                matiere = Matiere.objects.get(id=matiere_id)
                if quantite_retournee > matiere.remaining_quantity:
                    raise serializers.ValidationError(
                        {
                            "quantite_retournee": f"Cannot return {quantite_retournee} units. Only {matiere.remaining_quantity} remaining."
                        }
                    )
            except Matiere.DoesNotExist:
                raise serializers.ValidationError({"matiere_id": "Material not found."})

        return attrs


class ClientBasicSerializer(serializers.ModelSerializer):
    """Basic client serializer for BonRetour"""

    class Meta:
        model = Client
        fields = ["id", "nom_client", "numero_fiscal", "adresse"]


class BonRetourSerializer(serializers.ModelSerializer):
    """Main serializer for BonRetour"""

    client_details = ClientBasicSerializer(source="client", read_only=True)
    matiere_retours = MatiereRetourSerializer(many=True, required=False)
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
            "matiere_retours",
        ]
        read_only_fields = [
            "id",
            "date_creation",
            "derniere_mise_a_jour",
            "date_emission",
        ]

    def create(self, validated_data):
        """Create BonRetour with related MatiereRetour instances"""
        matiere_retours_data = validated_data.pop("matiere_retours", [])
        bon_retour = BonRetour.objects.create(**validated_data)

        # Create MatiereRetour instances
        for matiere_retour_data in matiere_retours_data:
            MatiereRetour.objects.create(bon_retour=bon_retour, **matiere_retour_data)

        return bon_retour

    def update(self, instance, validated_data):
        """Update BonRetour and related MatiereRetour instances"""
        matiere_retours_data = validated_data.pop("matiere_retours", [])

        # Update basic fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Handle matiere_retours update
        if matiere_retours_data is not None:
            # Clear existing relations
            instance.matiere_retours.all().delete()

            # Create new relations
            for matiere_retour_data in matiere_retours_data:
                MatiereRetour.objects.create(bon_retour=instance, **matiere_retour_data)

        return instance


class BonRetourListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing BonRetour"""

    client_name = serializers.CharField(source="client.nom_client", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    total_materials = serializers.SerializerMethodField()

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
            "total_materials",
        ]

    def get_total_materials(self, obj):
        """Get total number of different materials in this return"""
        return obj.matiere_retours.count()


class ClientMaterialsSerializer(serializers.ModelSerializer):
    """Serializer to show client's available materials for return"""

    available_materials = serializers.SerializerMethodField()

    class Meta:
        model = Client
        fields = ["id", "nom_client", "numero_fiscal", "available_materials"]

    def get_available_materials(self, obj):
        """Get all materials for this client that have remaining quantity > 0"""
        materials = obj.matieres.filter(remaining_quantity__gt=0)
        return MatiereForRetourSerializer(materials, many=True).data
