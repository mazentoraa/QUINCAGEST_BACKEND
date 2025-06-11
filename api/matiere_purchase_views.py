from rest_framework import viewsets, permissions, filters
from .models import MatierePurchase
from .matiere_purchase_serializers import MatierePurchaseSerializer


class MatierePurchaseViewSet(viewsets.ModelViewSet):
    queryset = MatierePurchase.objects.all()
    serializer_class = MatierePurchaseSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [ filters.SearchFilter, filters.OrderingFilter]
    
    filterset_fields = ['is_deleted']
    search_fields = ['nom', 'description' ]
    ordering_fields = ['date_creation', 'nom']
    ordering = ['-date_creation']