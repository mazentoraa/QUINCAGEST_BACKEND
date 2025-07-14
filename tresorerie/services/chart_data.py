from datetime import timedelta
from django.db.models import Sum
from api.models import Cd, FactureAchatMatiere, TraiteFournisseur, Traite

def compute_chart_data(start_date, end_date, labels, period_type):
    date_groups = []
    if period_type == "week":
        for i in range(7):
            d = start_date + timedelta(days=i)
            date_groups.append((d, d))
    elif period_type == "month":
        for i in range(4):
            start = start_date + timedelta(days=i*7)
            end = start + timedelta(days=6)
            date_groups.append((start, end))
    elif period_type == "quarter":
        for i in range(3):
            start = start_date + timedelta(days=i*30)
            end = start + timedelta(days=29)
            date_groups.append((start, end))
    elif period_type == "year":
        for i in range(4):
            start = start_date + timedelta(days=i*91)
            end = start + timedelta(days=90)
            date_groups.append((start, end))

    encaiss = []
    decaiss = []

    for start, end in date_groups:
        # Encaissements
        direct = Cd.objects.filter(
            statut='completed',
            date_commande__range=(start, end),
            mode_paiement__in=['cash', 'virement', 'cheque', 'carte']
        ).aggregate(total=Sum('montant_ttc'))['total'] or 0

        traite = Traite.objects.filter(
            status='PAYEE',
            date_echeance__range=(start, end)
        ).aggregate(total=Sum('montant'))['total'] or 0

        encaiss.append(round(direct + traite, 2))

        # Decaissements
        direct_d = FactureAchatMatiere.objects.filter(
            date_facture__range=(start, end),
            mode_paiement__in=['cash', 'virement', 'cheque', 'carte']
        ).aggregate(total=Sum('prix_total'))['total'] or 0

        traite_d = TraiteFournisseur.objects.filter(
            status='PAYEE',
            date_echeance__range=(start, end)
        ).aggregate(total=Sum('montant'))['total'] or 0

        decaiss.append(round(-(direct_d + traite_d), 2))

    return {
        "labels": labels,
        "encaissements": encaiss,
        "decaissements": decaiss
    }