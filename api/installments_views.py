from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import PlanTraite, Traite, Client, Cd
from .installments_serializers import (
    PlanTraiteSerializer,
    TraiteSerializer,
    CreatePlanTraiteSerializer,
    UpdateTraiteStatusSerializer
)


class PlanTraiteViewSet(viewsets.ModelViewSet):
    queryset = PlanTraite.objects.all().select_related('client')
    serializer_class = PlanTraiteSerializer

    def get_serializer_class(self):
        if self.action == 'create':
            return CreatePlanTraiteSerializer
        return super().get_serializer_class()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        numero_commande = validated_data.get('numero_commande')
        try:
            commande = Cd.objects.select_related('client').get(numero_commande=numero_commande)
            client = commande.client
        except Cd.DoesNotExist:
            return Response(
                {"numero_commande": ["Commande introuvable."]},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Création du PlanTraite avec fallback pour montant_total
        plan = PlanTraite.objects.create(
            client=client,
            numero_facture=numero_commande,
            nombre_traite=validated_data.get('nombre_traite'),
            date_premier_echeance=validated_data.get('date_premier_echeance'),
            periode=validated_data.get('periode', 30),
            montant_total=validated_data.get('montant_total') or commande.montant_ttc,
            nom_raison_sociale=client.nom_client,
            matricule_fiscal=client.numero_fiscal,
            rip=validated_data.get('rip', ''),
            acceptance=validated_data.get('acceptance', ''),
            notice=validated_data.get('notice', ''),
            bank_name=validated_data.get('bank_name', ''),
            bank_address=validated_data.get('bank_address', '')
        )

        # Création automatique des traites
        plan._create_traites()
        plan.save()

        return Response(PlanTraiteSerializer(plan).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'])
    def traites(self, request, pk=None):
        plan = self.get_object()
        traites = plan.traites.all()
        serializer = TraiteSerializer(traites, many=True)
        return Response(serializer.data)


class TraiteViewSet(viewsets.ModelViewSet):
    queryset = Traite.objects.all().select_related('plan_traite')
    serializer_class = TraiteSerializer

    @action(detail=True, methods=['patch'], url_path='update-status')
    def update_status(self, request, pk=None):
        traite = self.get_object()
        serializer = UpdateTraiteStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        traite.status = serializer.validated_data['status']
        traite.save()

        # Mise à jour du statut du plan selon l'état de toutes ses traites
        plan = traite.plan_traite
        all_status = [t.status for t in plan.traites.all()]

        if all(s == 'PAYEE' for s in all_status):
            plan.status = 'PAYEE'
        elif any(s == 'PAYEE' for s in all_status):
            plan.status = 'PARTIELLEMENT_PAYEE'
        else:
            plan.status = 'NON_PAYEE'

        plan.save()

        return Response(TraiteSerializer(traite).data)
