from django.db.models import Sum, F
from api.models import FactureTravaux, Cd, MatierePremiereAchat
from tresorerie.utils.dates import get_week_range
from decimal import Decimal

def compute_trend(model, date_field, filters=None, range_func=None, aggregate_expression=None, offset=0):
    """
    Computes value and trend between current and previous period.
    
    Params:
        model: Django model
        date_field: name of the date field to filter on
        filters: optional filter dict
        range_func: function(offset) → (start, end)
        aggregate_expression: optional dict to use in .aggregate() instead of default Sum('amount')
    """
    filters = filters or {}
    range_func = range_func or (lambda offset: (None, None))

    def get_total(offset):
        start, end = range_func(offset)
        qs = model.objects.filter(**filters)
        if start and end:
            qs = qs.filter(**{f"{date_field}__range": (start, end)})
        if aggregate_expression:
            return qs.aggregate(**aggregate_expression)['total'] or 0
        else:
            return qs.aggregate(total=Sum('amount'))['total'] or 0 # default

    curr_total = get_total(offset)
    prev_total = get_total(offset-1)

    trend = 0 if prev_total == 0 else ((curr_total - prev_total) / prev_total) * 100
    return round(curr_total, 3), round(trend, 1)

def compute_balance_trend(income_value, expense_value):
    # current balance
    current_balance = Decimal(income_value) - Decimal(expense_value)

    # previous week values
    prev_income, _ = compute_trend(
        model=Cd,
        date_field='date_commande',
        filters={'statut': 'completed'},
        range_func=get_week_range,
        aggregate_expression={'total': Sum('montant_ttc')},
        offset=-1
    )
    prev_expense, _ = compute_trend(
        model=MatierePremiereAchat,
        date_field='date_reception',
        range_func=get_week_range,
        aggregate_expression={'total': Sum(F('prix_unitaire') * F('remaining_quantity'))},
        offset=-1
    )

    previous_balance = Decimal(prev_income) - Decimal(prev_expense)

    # trend calculation
    if previous_balance == 0:
        trend = 0
    else:
        trend = ((current_balance - previous_balance) / previous_balance) * 100

    return round(current_balance, 3), round(trend, 1), round(previous_balance, 3)


def compute_forecast_trend(current_balance, previous_balance):
    adjustment = 10250  # arbiratry adjustment
    current_forecast = current_balance + adjustment
    previous_forecast = previous_balance + adjustment

    if previous_forecast == 0:
        trend = 0
    else:
        trend = ((current_forecast - previous_forecast) / previous_forecast) * 100

    return round(current_forecast, 3), round(trend, 1)


def compute_kpis():
    """
    This function aggregates KPI values such as balance, income, expense, and forecast.
    """
    
    income_value, income_trend = compute_trend(
        model=Cd,
        date_field='date_commande',
        filters={'statut': 'completed'},
        range_func=get_week_range,
        aggregate_expression={'total': Sum('montant_ttc')}
    )
    expense_value, expense_trend = compute_trend(
        model=MatierePremiereAchat,
        date_field='date_reception',
        range_func=get_week_range,
        aggregate_expression={'total': Sum(F('prix_unitaire') * F('remaining_quantity'))}
    )
    balance_value, balance_trend, previous_balance = compute_balance_trend(income_value, expense_value)
    forecast_value, forecast_trend = compute_forecast_trend(balance_value, previous_balance)

    return {
        "balance": {"value": balance_value, "trend": balance_trend, "positive": balance_value >= 0},
        "income": {"value": income_value, "trend": income_trend, "positive": income_trend >= 0},
        "expense": {"value": expense_value, "trend": expense_trend, "positive": False},
        "forecast": {"value": forecast_value, "trend": forecast_trend, "positive": forecast_trend >= 0},
    }