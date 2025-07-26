from django.db.models import Sum, F
from datetime import date, timedelta    
from django.utils.timezone import now
from api.models import Avoir, Cd, Devis, Traite, TraiteFournisseur, Avance, FichePaie, Achat, FactureAchatMatiere, PlanTraiteFournisseur
from api.utils.dates import get_week_range
from api.services.schedule_service import get_schedule
from decimal import Decimal

def get_period_range(range_func, offset=0):
    return range_func(offset)

def compute_income(range_func, offset=0):
    start_date, end_date = get_period_range(range_func, offset)

    # Facture client payees
    cd_total = compute_total( 
        model=Cd,
        date_field='date_commande',
        filters={'statut': 'completed', 'is_deleted': False},
        exclude_filters={'mode_paiement__in': ['mixte', 'traite']}, 
        date_range=(start_date, end_date),
        aggregate_expression={'total': Sum('montant_ttc')}
    )
    # Facture client mode_paiement mixte partie comptant
    cd_mixte_total = compute_total( 
        model=Cd,
        date_field='date_commande',
        filters={'statut': 'completed', 'mode_paiement':'mixte','is_deleted': False},
        date_range=(start_date, end_date),
        aggregate_expression={'total': Sum('mixte_comptant')}
    )
    # Traites client
    traite_total = compute_total(
        model=Traite,
        date_field='date_echeance',
        filters={'status': 'PAYEE'},
        date_range=(start_date, end_date),
        aggregate_expression={'total': Sum('montant')}
    )
    # Remboursement avoir fournisseur
    remb_total = compute_total( 
        model=Avoir,
        date_field='date_avoir',
        filters={'date_avoir__lte': now().date()},
        date_range=(start_date, end_date),
        aggregate_expression={'total': Sum('montant_total')}
    )
    print('Total factures client : ', cd_total)
    print('Total factures mixtes client : ', cd_mixte_total)
    print('Total traites client : ', traite_total)
    print('Total remboursements avoirs : ', traite_total)
    total_income = Decimal(cd_total) + Decimal(cd_mixte_total) + Decimal(traite_total) + Decimal(remb_total)
    return total_income

def compute_expenses(start_date, end_date):
    
    # Factures fournisseurs réglées (mode_paiement != "traite")
    factures_payees_total = compute_total(
            model=FactureAchatMatiere,
            date_field='date_facture',
            filters={'date_facture__lte': now().date()},
            exclude_filters={'mode_paiement__in': ['mixte','traite']},
            date_range=(start_date, end_date),
            aggregate_expression={'total': Sum('prix_total')}
        )
    # Factures fournisseurs réglées (mode_paiement == "mixte"), adding part comptant
    paiement_mixte_total = compute_total(
            model=FactureAchatMatiere,
            date_field='date_facture',
            filters={'date_facture__lte': now().date(), 'mode_paiement':'mixte'},
            date_range=(start_date, end_date),
            aggregate_expression={'total': Sum('mixte_comptant')}
        )

    # 4. Traites fournisseurs payées
    traites_fournisseur_total = compute_total(
            model=TraiteFournisseur,
            date_field='date_echeance',
            filters={'status': 'PAYEE'},
            date_range=(start_date, end_date),
            aggregate_expression={'total': Sum('montant')}
        )

    # 5. Salaires payés (net à payer)
    salaires_payes_total = compute_total(
            model=FichePaie,
            date_field='date_creation',
            date_range=(start_date, end_date),
            aggregate_expression={'total': Sum('net_a_payer')}
        )

    # 6. Avances versées non remboursées
    avances = Avance.objects.filter(
        date_demande__range=(start_date, end_date),
        statut='Acceptée'
    )
    total = 0
    for avance in avances:
        rembourse = avance.remboursements.aggregate(r=Sum('montant'))['r'] or 0
        total += max(0, avance.montant - rembourse)
    avances_non_remboursees_total = total
    
    print('Total factures fournisseur payées: ', factures_payees_total)
    print('Total paiement fournisseur mixte: ', paiement_mixte_total)
    print('Total traites fournisseur: ', traites_fournisseur_total)
    print('Total salaires payés: ', salaires_payes_total)
    print('Total avances non remboursées: ', avances_non_remboursees_total)

    return (
        Decimal(factures_payees_total) + Decimal(paiement_mixte_total) + Decimal(traites_fournisseur_total) + Decimal(salaires_payes_total) + Decimal(avances_non_remboursees_total)
    )
def compute_expected_income(start_date, end_date):

    # Factures clients non payées hors traite
    factures_non_payees = compute_total(
        model=Cd,
        date_field='date_commande',
        filters={'is_deleted': False, 'nature':'facture', 'date_commande__gt': now().date()},
        exclude_filters={'mode_paiement': 'traite', 'statut': 'completed'},
        aggregate_expression={'total': Sum('montant_ttc')}
    )
    
    # Traites clients non payées
    traites_non_payees = compute_total(
        model=Traite,
        date_field='date_echeance',
        filters={'status': 'NON_PAYEE'},
        aggregate_expression={'total': Sum('montant')}
    )

    # Devis acceptés
    devis_acceptes = compute_total(
        model=Devis,
        date_field='date_emission',
        filters={'statut': 'accepted'},
        aggregate_expression={'total': Sum('montant_ttc')}
    )

    print('Total achats payés: ', factures_non_payees)
    print('Total factures payées: ', traites_non_payees)
    print('Total paiement mixte: ', devis_acceptes)

    return (
        Decimal(factures_non_payees) + Decimal(traites_non_payees) + Decimal(devis_acceptes)
    )

def compute_expected_expenses(start_date, end_date):

    # Factures fournisseurs non payées
    factures_fournisseur_non_payees = compute_total(
        model=FactureAchatMatiere,
        date_field='date_facture',
        filters={'date_facture__gt': now().date()},
        aggregate_expression={'total': Sum('prix_total')}
    )
    
    # Traites fournisseurs non payées
    traites_fournisseurs_non_payees = compute_total(
        model=TraiteFournisseur,
        date_field='date_echeance',
        filters={'status': 'NON_PAYEE'},
        aggregate_expression={'total': Sum('montant')}
    )

    # Salaires à payer
    salaires_a_payer = compute_total(
        model=FichePaie,
        date_field='mois',
        filters={'statut': 'Générée'},
        aggregate_expression={'total': Sum('net_a_payer')}
    )
    
    #  Avances à verser
    avances_a_verser = compute_total(
        model=Avance,
        date_field='date_demande',
        filters={'statut': 'Acceptée'}, 
        aggregate_expression={'total': Sum('montant')}
    )

    print('Total factures fournisseur non payés : ', factures_fournisseur_non_payees)
    print('Total traites fournisseurs non payées: ', traites_fournisseurs_non_payees)
    print('Total salaires à payer: ', salaires_a_payer)
    print('Total avances à verser: ', avances_a_verser)

    return (
        Decimal(factures_fournisseur_non_payees) + Decimal(traites_fournisseurs_non_payees) + Decimal(salaires_a_payer) + Decimal(avances_a_verser)
    )

def compute_total(model, date_field, filters=None, exclude_filters=None, date_range=None, aggregate_expression=None):
    filters = filters or {}
    qs = model.objects.filter(**filters)
    if exclude_filters:
        qs = qs.exclude(**exclude_filters)
    if date_range:
        start_date, end_date = date_range
        qs = qs.filter(**{f"{date_field}__range": (start_date, end_date)})
    if aggregate_expression:
        return qs.aggregate(**aggregate_expression).get('total') or 0
    return qs.aggregate(total=Sum('amount')).get('total') or 0

def compute_income_trend(range_func):
    curr_income = compute_income(range_func, offset=0)
    prev_income = compute_income(range_func, offset=1)  

    if prev_income == 0:
        trend = 0.0 if curr_income == 0 else 100.0
    else:
        trend = ((curr_income - prev_income) / prev_income) * 100

    return round(curr_income, 3), round(trend, 2), round(prev_income, 3)

def compute_expense_trend(range_func):
    curr_start, curr_end = range_func(0)
    prev_start, prev_end = range_func(1)

    curr_exp = compute_expenses(curr_start, curr_end)
    prev_exp = compute_expenses(prev_start, prev_end)

    trend = ((curr_exp - prev_exp) / prev_exp * 100) if prev_exp != 0 else (100 if curr_exp else 0)

    return round(curr_exp, 3), round(trend, 2), round(prev_exp, 3)

def compute_expected_income_trend(range_func):
    curr_start, curr_end = range_func(0)
    prev_start, prev_end = range_func(1)

    curr_expected_income = compute_expected_income(curr_start, curr_end)
    prev_expected_income = compute_expected_income(prev_start, prev_end)

    trend = ((curr_expected_income - prev_expected_income) / prev_expected_income * 100) if prev_expected_income != 0 else (100 if curr_expected_income else 0)

    return round(curr_expected_income, 3), round(trend, 2), round(prev_expected_income, 3)

def compute_expected_expenses_trend(range_func):
    curr_start, curr_end = range_func(0)
    prev_start, prev_end = range_func(1)

    curr_expected_income = compute_expected_expenses(curr_start, curr_end)
    prev_expected_income = compute_expected_expenses(prev_start, prev_end)

    trend = ((curr_expected_income - prev_expected_income) / prev_expected_income * 100) if prev_expected_income != 0 else (100 if curr_expected_income else 0)

    return round(curr_expected_income, 3), round(trend, 2), round(prev_expected_income, 3)

def compute_balance_trend(income_value, expense_value):
    # Current balance
    current_balance = Decimal(income_value) - Decimal(expense_value)

    # Previous period
    prev_income = compute_income(get_week_range, offset=1)

    prev_start, prev_end = get_week_range(1)
    prev_expense = compute_expenses(prev_start, prev_end)

    # Previous balance
    previous_balance = Decimal(prev_income) - Decimal(prev_expense)

    # Trend
    if previous_balance == 0:
        trend = 0
    else:
        trend = ((current_balance - previous_balance) / previous_balance) * 100

    return round(current_balance, 3), round(trend, 1), round(previous_balance, 3)

# Solde prévisionnel
def compute_forecast_trend(current_balance, previous_balance, expected_income_value, previous_expected_income, expected_expenses_value, previous_expected_expenses):
    current_forecast = current_balance + expected_income_value - expected_expenses_value
    previous_forecast = previous_balance + previous_expected_income - previous_expected_expenses

    if previous_forecast == 0:
        trend = 0
    else:
        trend = ((current_forecast - previous_forecast) / previous_forecast) * 100

    return round(current_forecast, 3), round(trend, 1)

# Evolution de la Trésorerie
def get_week_label(start_date):
    return start_date.strftime("%d/%m")

def get_treasury_evolution_weeks(evolution_weeks):
    today = date.today()
    treasury_balances = []
    labels = []

    # Number of weeks to include
    def period_to_num_weeks(period: str) -> int:
        if period == "90d":
            return 13  
        elif period == "1y":
            return 52
        return 4  # default: 30d = 4 weeks
    num_weeks = period_to_num_weeks(evolution_weeks)

    for week_offset in reversed(range(num_weeks)):
        start_date, end_date = get_week_range(offset_weeks=-week_offset)

        # Prepare range_func to pass to compute functions
        def range_func(offset):
            return get_week_range(offset_weeks=-offset)

        # Manually compute date range for labels and compute_expenses
        start_date, end_date = get_week_range(offset_weeks=-week_offset)

        labels.append(get_week_label(start_date))
        income = compute_income(range_func, offset=week_offset)
        expenses = compute_expenses(start_date, end_date)

        # Compute balance
        balance = income - expenses

        treasury_balances.append(balance)
    # Format data for chart.js
    treasury_chart_data = {
        "labels": labels,
        "datasets": [{
            "label": "Solde de Trésorerie",
            "data": treasury_balances,
            "borderColor": "#10b981",
            "backgroundColor": "rgba(16, 185, 129, 0.1)",
            "borderWidth": 3,
            "fill": True,
            "tension": 0.4,
            "pointBackgroundColor": "#10b981",
            "pointBorderColor": "#ffffff",
            "pointBorderWidth": 2,
            "pointRadius": 6,
        }]
    }

    return treasury_chart_data

def get_total_transactions_count(range_func):
    
    def this_week_range_func(field):
        start, end = range_func() # This week
        return {f"{field}__range": (start, end)}
    total = 0

    total += Cd.objects.filter(**this_week_range_func("date_commande")).count()
    total += Traite.objects.filter(**this_week_range_func("date_echeance")).count()
    total += FactureAchatMatiere.objects.filter(**this_week_range_func("date_facture")).count()
    total += TraiteFournisseur.objects.filter(**this_week_range_func("date_echeance")).count()
    total += FichePaie.objects.filter(**this_week_range_func("date_creation")).count()
    total += Avance.objects.filter(**this_week_range_func("date_demande")).count()

    return total

def get_taux_de_recouvrement(range_func):

    def this_week_range_func(field):
        start, end = range_func()
        return {f"{field}__range": (start, end)}

    # Total amount of client invoices issued (factures)
    total_issued = Cd.objects.filter(**this_week_range_func("date_commande"), statut='completed', is_deleted=False).aggregate(
        total=Sum("montant_ttc")
    )["total"] or 0

    # Total amount of payments received for client invoices (encaissements)
    total_received = Cd.objects.filter(**this_week_range_func("date_commande"), is_deleted=False).aggregate(
        total=Sum("montant_ttc")
    )["total"] or 0

    if total_issued == 0:
        return 0.0  # Avoid division by zero

    taux = (total_received / total_issued) * 100
    return round(taux, 2)


def generate_alerts(forecast, balance, expected_income, expected_expense):
    alerts = []

    schedule = get_schedule()

    # ⚠️ Alert 1: Solde critique
    if forecast < 5000:
        alerts.append({
            "type": "critical",
            "title": "Solde critique prévu",
            "description": f"Solde prévisionnel faible : {forecast} DT (seuil: 5,000 DT)",
        })

    # ⚠️ Alert 2: Solde net négatif
    if balance < 0:
        alerts.append({
            "type": "danger",
            "title": "Solde actuel négatif",
            "description": f"Solde de trésorerie actuel est négatif : {balance} DT",
        })

    # ⚠️ Alert 3: Dépenses prévues supérieures aux recettes attendues
    if expected_expense > expected_income:
        delta = expected_expense - expected_income
        alerts.append({
            "type": "warning",
            "title": "Dépenses prévues > Recettes attendues",
            "description": f"Écart de {delta} DT entre les dépenses ({expected_expense}) et les recettes ({expected_income}) attendues.",
        })

    # ℹ️ Alert 4: Evénements à venir importants
    for item in schedule:
        amount = Decimal(item["amount"])
        if amount < -10000:
            alerts.append({
                "type": "info",
                "title": "Dépense importante à venir",
                "description": f"{item['description']} le {item['date']} ({-amount} DT)",
            })
        elif amount > 10000:
            alerts.append({
                "type": "info",
                "title": "Encaissement important prévu",
                "description": f"{item['description']} le {item['date']} (+{amount} DT)",
            })

    return alerts


def compute_kpis(evolution_weeks):
    """
    This function aggregates KPI values such as balance, income, expense, and forecast.
    """
    income_value, income_trend, previous_income = compute_income_trend(get_week_range)
    print('Income value: ', income_value, ' | Income trend: ', income_trend)
    

    expenses_value, expenses_trend, previous_expenses = compute_expense_trend(get_week_range)
    print('Expenses value: ', expenses_value, ' | Expenses trend: ', expenses_trend)

    balance_value, balance_trend, previous_balance = compute_balance_trend(income_value, expenses_value)
    print('Balance value: ', balance_value, ' | Balance trend: ', balance_trend)

    expected_expenses_value, expected_expenses_trend, previous_expected_expenses = compute_expected_expenses_trend(get_week_range)
    print('Expected income value: ', expected_expenses_value, ' | Income trend: ', expected_expenses_trend)
    
    expected_income_value, expected_income_trend, previous_expected_income = compute_expected_income_trend(get_week_range)
    print('Expected income value: ', expected_income_value, ' | Income trend: ', expected_income_trend)

    forecast_value, forecast_trend = compute_forecast_trend(balance_value, previous_balance, expected_income_value, previous_expected_income, expected_expenses_value, previous_expected_expenses)
    print('Forecast value: ', str(forecast_value), ' | Forecast trend: ', str(forecast_trend))

    return {
        "balance": {"value": balance_value, "trend": balance_trend, "positive": balance_value >= 0},
        "income": {"value": income_value, "trend": income_trend, "positive": income_trend >= 0},
        "expense": {"value": expenses_value, "trend": expenses_trend, "positive": False},
        "expected_income": {"value": expected_income_value, "trend": expected_income_trend, "positive": expected_income_trend >= 0},
        "expected_expense": {"value": expected_expenses_value, "trend": expected_expenses_trend, "positive": expected_expenses_trend >= 0},
        "forecast": {"value": forecast_value, "trend": forecast_trend, "positive": forecast_trend >= 0},
        "treasury_chart_data": get_treasury_evolution_weeks(evolution_weeks),
        "nb_transactions": get_total_transactions_count(get_week_range),
        "taux_de_recouvrement": get_taux_de_recouvrement(get_week_range),
        "alerts": generate_alerts(forecast_value, balance_value, expected_income_value, expected_expenses_value)
    }