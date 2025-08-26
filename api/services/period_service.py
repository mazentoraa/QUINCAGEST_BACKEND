from datetime import date, timedelta
from django.db.models import Sum, Q
from api.models import Traite, Cd, FactureAchatProduit, TraiteFournisseur
from api.utils.dates import get_week_range
from decimal import Decimal

def compute_encaissements(start_date, end_date):
    # 1. Factures payées directement (cash, virement, etc.)
    direct_total = Cd.objects.filter(
        statut='completed',
        date_commande__range=(start_date, end_date),
        mode_paiement__in=['cash', 'virement', 'cheque', 'carte']
    ).aggregate(total=Sum('montant_ttc'))['total'] or 0

    # 2. Traites payées pendant la période
    traite_total = Traite.objects.filter(
        status='PAYEE',
        date_echeance__range=(start_date, end_date)
    ).aggregate(total=Sum('montant'))['total'] or 0

    return round(direct_total + traite_total, 3)


def compute_encaissement_trend(start_curr, end_curr):
    # Previous period based on same duration
    delta = end_curr - start_curr
    start_prev = start_curr - delta - timedelta(days=1)
    end_prev = start_curr - timedelta(days=1)

    curr_total = compute_encaissements(start_curr, end_curr)
    prev_total = compute_encaissements(start_prev, end_prev)

    if prev_total == 0:
        trend = 0
    else:
        trend = round(((curr_total - prev_total) / abs(prev_total)) * 100, 1)

    return curr_total, trend


def compute_decaissements(start_date, end_date):
    # 1. Direct payments (cash, virement, cheque, carte)
    direct_total = FactureAchatMatiere.objects.filter(
        # statut='payée',
        date_facture__range=(start_date, end_date),
        mode_paiement__in=['cash', 'virement', 'cheque', 'carte']
    ).aggregate(total=Sum('prix_total'))['total'] or 0

    # 2. Traites fournisseurs payées
    traite_total = TraiteFournisseur.objects.filter(
        status='PAYEE',
        date_echeance__range=(start_date, end_date)
    ).aggregate(total=Sum('montant'))['total'] or 0

    return round(direct_total + traite_total, 3)


def compute_decaissement_trend(start_curr, end_curr):
    delta = end_curr - start_curr
    start_prev = start_curr - delta - timedelta(days=1)
    end_prev = start_curr - timedelta(days=1)

    curr_total = compute_decaissements(start_curr, end_curr)
    prev_total = compute_decaissements(start_prev, end_prev)

    if prev_total == 0:
        trend = 0
    else:
        trend = round(((curr_total - prev_total) / abs(prev_total)) * 100, 1)

    return curr_total, trend

def compute_resultat_net_trend(start_curr, end_curr):

    delta = end_curr - start_curr
    start_prev = start_curr - delta - timedelta(days=1)
    end_prev = start_curr - timedelta(days=1)

    # Compute current week values
    curr_encaissements = compute_encaissements(start_curr, end_curr)
    curr_decaissements = compute_decaissements(start_curr, end_curr)
    curr_result = Decimal(curr_encaissements) - Decimal(curr_decaissements)

    # Compute previous week values
    prev_encaissements = compute_encaissements(start_prev, end_prev)
    prev_decaissements = compute_decaissements(start_prev, end_prev)
    prev_result = Decimal(prev_encaissements) - Decimal(prev_decaissements)

    # Trend
    if prev_result == 0:
        trend = 0
    else:
        trend = round(((curr_result - prev_result) / abs(prev_result)) * 100, 1)

    return round(curr_result, 3), trend

def compute_traites_fournisseurs_total(start_date, end_date):
    return TraiteFournisseur.objects.filter(
        status='PAYEE',
        date_echeance__range=(start_date, end_date)
    ).aggregate(total=Sum('montant'))['total'] or 0

def compute_traites_fournisseurs_trend(start_curr, end_curr):
    delta = end_curr - start_curr
    start_prev = start_curr - delta - timedelta(days=1)
    end_prev = start_curr - timedelta(days=1)

    curr_total = compute_traites_fournisseurs_total(start_curr, end_curr)
    prev_total = compute_traites_fournisseurs_total(start_prev, end_prev)

    if prev_total == 0:
        trend = 0
    else:
        trend = round(((curr_total - prev_total) / abs(prev_total)) * 100, 1)

    return round(curr_total, 3), trend

def compute_traites_clients_total(start_date, end_date):
    return Traite.objects.filter(
        status='PAYEE',
        date_echeance__range=(start_date, end_date)
    ).aggregate(total=Sum('montant'))['total'] or 0

def compute_traites_clients_trend(start_curr, end_curr):
    delta = end_curr - start_curr
    start_prev = start_curr - delta - timedelta(days=1)
    end_prev = start_curr - timedelta(days=1)

    curr_total = compute_traites_clients_total(start_curr, end_curr)
    prev_total = compute_traites_clients_total(start_prev, end_prev)

    if prev_total == 0:
        trend = 0
    else:
        trend = round(((curr_total - prev_total) / abs(prev_total)) * 100, 1)

    return round(curr_total, 3), trend

def compute_echues_total_and_count_with_trend(start_curr, end_curr):
    today = date.today()
    delta = end_curr - start_curr
    start_prev = start_curr - delta - timedelta(days=1)
    end_prev = start_curr - timedelta(days=1)

    # Clients - current week échues
    echues_clients_curr = Traite.objects.filter(
        status="NON_PAYEE",
        date_echeance__lt=today,
        date_echeance__range=(start_curr, end_curr)
    )
    # Clients - previous week échues
    echues_clients_prev = Traite.objects.filter(
        status="NON_PAYEE",
        date_echeance__lt=today,
        date_echeance__range=(start_prev, end_prev)
    )

    # Fournisseurs - current
    echues_fournisseurs_curr = TraiteFournisseur.objects.filter(
        status__in=["NON_PAYEE", "PARTIELLEMENT_PAYEE"],
        date_echeance__lt=today,
        date_echeance__range=(start_curr, end_curr)
    )
    # Fournisseurs - previous
    echues_fournisseurs_prev = TraiteFournisseur.objects.filter(
        status__in=["NON_PAYEE", "PARTIELLEMENT_PAYEE"],
        date_echeance__lt=today,
        date_echeance__range=(start_prev, end_prev)
    )

    # Totals
    curr_total = (
        echues_clients_curr.aggregate(total=Sum("montant"))["total"] or 0
    ) + (
        echues_fournisseurs_curr.aggregate(total=Sum("montant"))["total"] or 0
    )
    prev_total = (
        echues_clients_prev.aggregate(total=Sum("montant"))["total"] or 0
    ) + (
        echues_fournisseurs_prev.aggregate(total=Sum("montant"))["total"] or 0
    )

    # Counts (for UI info)
    curr_count = echues_clients_curr.count() + echues_fournisseurs_curr.count()

    # Trend
    if prev_total == 0:
        trend = 0
    else:
        trend = round(((curr_total - prev_total) / abs(prev_total)) * 100, 1)

    return round(curr_total, 3), curr_count, trend
