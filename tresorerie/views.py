from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .services.kpi_service import compute_kpis
from .services.schedule_service import get_schedule
from .services.traite_service import get_all_traites
from .services.period_service import (compute_encaissement_trend, compute_decaissement_trend, compute_resultat_net_trend, compute_traites_fournisseurs_trend, compute_traites_clients_trend, compute_echues_total_and_count_with_trend)
from .services.chart_data import compute_chart_data
from .utils.dates import get_period_range

class PeriodView(APIView):
    def get(self, request):
        period = request.query_params.get("period", "week")
        start_date, end_date, label = get_period_range(period)

        period_labels = {
            "week": "Cette semaine",
            "month": "Ce mois",
            "quarter": "Ce trimestre",
            "year": "Cette année"
        }
        label = period_labels.get(period, "Cette période")

        income, income_trend = compute_encaissement_trend(start_date, end_date)
        expense, expense_trend = compute_decaissement_trend(start_date, end_date)
        net, net_trend = compute_resultat_net_trend(start_date, end_date)
        traites_fournisseurs, traites_trend = compute_traites_fournisseurs_trend(start_date, end_date)
        traites_clients, traites_clients_trend = compute_traites_clients_trend(start_date, end_date)
        echues_total, echues_count, echues_trend = compute_echues_total_and_count_with_trend(start_date, end_date)
        chart_data = compute_chart_data(start_date, end_date, label, period)

        return Response({
            "encaissements": {
                "value": income,
                "trend": income_trend,
                "positive": income_trend >= 0,
                "label": label
            },
            "decaissements": {
                "value": -expense,
                "trend": -expense_trend,
                "positive": False,
                "label": label
            },
            "resultatNet": {
                "value": net,
                "trend": net_trend,
                "positive": net_trend >= 0,
                "label": label
            },
            "traitesFournisseurs": {
                "value": -traites_fournisseurs,
                "trend": -traites_trend,
                "positive": False,
                "label": label
            },
            "traitesClients": {
                "value": traites_clients,
                "trend": traites_clients_trend,
                "positive": traites_clients_trend >= 0,
                "label": label
            },
            "echues": {
                "value": echues_total,
                "trend": echues_trend,
                "count": echues_count,
                "positive": False,
                "label": label
            },
            "chart_data": chart_data
        })



class TraiteView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = get_all_traites()
        return Response(data)

class KPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = compute_kpis()
        return Response(data)

class ScheduleView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = get_schedule()
        return Response(data)