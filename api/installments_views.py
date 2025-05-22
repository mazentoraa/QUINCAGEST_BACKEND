from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import PlanTraite, Traite
from .installments_serializers import (
    PlanTraiteSerializer, 
    TraiteSerializer,
    CreatePlanTraiteSerializer,
    UpdateTraiteStatusSerializer
)
from datetime import timedelta

class PlanTraiteViewSet(viewsets.ModelViewSet):
    queryset = PlanTraite.objects.all().select_related('facture')
    serializer_class = PlanTraiteSerializer
    
    def get_serializer_class(self):
        if self.action == 'create':
            return CreatePlanTraiteSerializer
        return super().get_serializer_class()
    
    def create(self, request, *args, **kwargs):
        serializer = CreatePlanTraiteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        facture = FactureTravaux.objects.get(pk=serializer.validated_data['facture_id'])
        
        plan = PlanTraite.objects.create(
            facture=facture,
            nombre_traite=serializer.validated_data['nombre_traite'],
            date_premier_echeance=serializer.validated_data['date_premier_echeance'],
            periode=serializer.validated_data.get('periode', 30),
            montant_total=facture.montant_ttc,
            nom_raison_sociale=facture.client.nom_raison_sociale,
            matricule_fiscal=facture.client.matricule_fiscal
        )
        
        return Response(
            PlanTraiteSerializer(plan).data, 
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['get'])
    def traites(self, request, pk=None):
        plan = self.get_object()
        traites = plan.traites.all()
        serializer = TraiteSerializer(traites, many=True)
        return Response(serializer.data)

class TraiteViewSet(viewsets.ModelViewSet):
    queryset = Traite.objects.all().select_related('plan_traite')
    serializer_class = TraiteSerializer
    
    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
        traite = self.get_object()
        serializer = UpdateTraiteStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        traite.status = serializer.validated_data['status']
        traite.save()
        plan = traite.plan_traite
        if plan.traites.filter(status='NON_PAYEE').count() == 0:
            plan.status = 'PAYEE'
            plan.save()
        
        return Response(TraiteSerializer(traite).data)