from rest_framework import serializers
from .models import MatierePurchase

class MatierePurchaseSerializer(serializers.ModelSerializer):
    # type_matiere = models.CharField(max_length=50, blank=True, null=True)  # Gardez temporairement
    # nom = models.CharField(max_length=100, blank=True)
    class Meta:
        model = MatierePurchase
        fields = [
            'id',
            'nom',
            'description',
            'prix_unitaire',
            'quantite',
            'date_creation',
            'derniere_mise_a_jour',
            'purshase_date',
            'is_deleted',
            'deleted_at',
        ]
        read_only_fields = ['date_creation', 'derniere_mise_a_jour']

    
