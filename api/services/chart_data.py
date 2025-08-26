from datetime import timedelta
from django.db.models import Sum
from api.models import Cd, FactureAchatProduit, TraiteFournisseur, Traite
from .kpi_service import compute_kpis

def compute_chart_data(start_date, end_date, labels, period_type):
    date_groups = []
    evolution_weeks = '7d'
    if period_type == "week":
        # Adjust to Monday of the week
        monday = start_date - timedelta(days=start_date.weekday())
        for i in range(6):  # Monday to Saturday
            d = monday + timedelta(days=i)
            date_groups.append((d, d))
    elif period_type == "month":
        for i in range(4):
            start = start_date + timedelta(days=i*7)
            end = start + timedelta(days=6)
            date_groups.append((start, end))
            evolution_weeks = '30d'
    elif period_type == "quarter":
        for i in range(3):
            start = start_date + timedelta(days=i*30)
            end = start + timedelta(days=29)
            date_groups.append((start, end))
            evolution_weeks = '90d'
    elif period_type == "year":
        for i in range(4):
            start = start_date + timedelta(days=i*91)
            end = start + timedelta(days=90)
            date_groups.append((start, end))
            evolution_weeks = '1y'
    # Dynamically override the default range_func
    def range_func(offset):
        return date_groups[0][0], date_groups[-1][0]
    
    kpis = compute_kpis(evolution_weeks=evolution_weeks, range_func=range_func)
    chart_data = kpis.get("treasury_chart_data", {})

    return {
        "labels": chart_data.get("labels", labels), 
        "encaissements": (kpis["income"]['value'], []),
        "decaissements": (kpis["expense"]['value'], [])
    }