from rest_framework import serializers
from .models import Client, Traveaux, Produit, Matiere, MatiereUsage
from django.db import transaction


class MatiereSerializer(serializers.ModelSerializer):
    client_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Matiere
        fields = (
            "id",
            "type_matiere",
            "description",
            "prix_unitaire",
            "client_id",
            "date_creation",
            "quantite",
            "derniere_mise_a_jour",
        )
        extra_kwargs = {
            'type_matiere': {'required': True},
            'description': {'required': False},
            'prix_unitaire': {'required': False},
            'client_id': {'required': True}
        }
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


class MatiereUsageSerializer(serializers.ModelSerializer):
    matiere_id = serializers.IntegerField()
    
    class Meta:
        model = MatiereUsage
        fields = ('matiere_id', 'quantite_utilisee')


class TraveauxSerializer(serializers.ModelSerializer):
    client_id = serializers.IntegerField()
    produit_id = serializers.IntegerField()
    client_name = serializers.CharField(source='client.nom_client', read_only=True)
    produit_name = serializers.CharField(source='produit.nom_produit', read_only=True)
    matiere_usages = MatiereUsageSerializer(many=True, required=False)

    class Meta:
        model = Traveaux
        fields = [
            "id",
            "client_id",
            "produit_id",
            "client_name",
            "produit_name",
            "duree",
            "quantite",
            "description",
            "date_creation",
            "matiere_usages",  # Ce champ doit être explicitement listé ici
            "derniere_mise_a_jour",
        ]
        read_only_fields = ("date_creation", "derniere_mise_a_jour", "client_name", "produit_name")
        extra_kwargs = {
            'duree': {'required': True},
            'quantite': {'required': True}
        }
    @transaction.atomic
    def create(self, validated_data):
        client_id = validated_data.pop("client_id")
        produit_id = validated_data.pop("produit_id")
        matiere_usages_data = validated_data.pop('matiere_usages', [])
        
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
            matiere_id = matiere_usage_data.get('matiere_id')
            quantite_utilisee = matiere_usage_data.get('quantite_utilisee')
            
            try:
                matiere = Matiere.objects.get(pk=matiere_id)
                
                # Vérifier si la matière appartient au bon client
                if matiere.client_id != client_id:
                    raise serializers.ValidationError(f"Le matériel avec ID {matiere_id} n'appartient pas au client sélectionné.")
                
                # Check if we have enough quantity - important: compare with remaining_quantity
                if matiere.remaining_quantity < quantite_utilisee:
                    raise serializers.ValidationError(f"Quantité insuffisante de matériel. Seulement {matiere.remaining_quantity} unités de {matiere.type_matiere} disponibles.")
                
                # Create the usage record
                MatiereUsage.objects.create(
                    travaux=travaux,
                    matiere=matiere,
                    quantite_utilisee=quantite_utilisee
                )
                
                # Update the remaining quantity
                matiere.remaining_quantity = matiere.remaining_quantity - quantite_utilisee
                matiere.save(update_fields=['remaining_quantity'])
                
            except Matiere.DoesNotExist:
                raise serializers.ValidationError(f"Matériel avec ID {matiere_id} introuvable")
        
        return travaux

    @transaction.atomic
    def update(self, instance, validated_data):
        if 'matiere_usages' in validated_data:
            matiere_usages_data = validated_data.pop('matiere_usages')
            
            # Reset quantities for existing usages first
            for usage in instance.matiere_usages.all():
                matiere = usage.matiere
                matiere.remaining_quantity = matiere.remaining_quantity + usage.quantite_utilisee
                matiere.save(update_fields=['remaining_quantity'])
                usage.delete()
            
            # Add new usages
            client_id = instance.client_id  # Utiliser l'ID client existant
            for matiere_usage_data in matiere_usages_data:
                matiere_id = matiere_usage_data.get('matiere_id')
                quantite_utilisee = matiere_usage_data.get('quantite_utilisee')
                try:
                    matiere = Matiere.objects.get(pk=matiere_id)
                    
                    # Vérifier si la matière appartient au bon client
                    if matiere.client_id != client_id:
                        raise serializers.ValidationError(f"Le matériel avec ID {matiere_id} n'appartient pas au client sélectionné.")

                    # Check if we have enough quantity
                    if matiere.remaining_quantity < quantite_utilisee:
                        raise serializers.ValidationError(f"Quantité insuffisante de matériel. Seulement {matiere.remaining_quantity} unités de {matiere.type_matiere} disponibles.")
                    
                    # Create the usage record
                    MatiereUsage.objects.create(
                        travaux=instance,
                        matiere=matiere,
                        quantite_utilisee=quantite_utilisee
                    )
                    
                    # Update the remaining quantity
                    matiere.remaining_quantity = matiere.remaining_quantity - quantite_utilisee
                    matiere.save(update_fields=['remaining_quantity'])
                    
                except Matiere.DoesNotExist:
                    raise serializers.ValidationError(f"Matériel avec ID {matiere_id} introuvable")
        
        # Process other fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        return instance