from datetime import date
from django.utils.timezone import now
from api.models import Cd, TraiteFournisseur, FichePaie, Traite


def get_schedule(end_date=None):
    today = date.today()
    upcoming_events = []

    # Date filter
    if end_date:
        cd_filter = {'date_commande__range': (today, end_date)}
        traite_filter = {'date_echeance__range': (today, end_date)}
        salaire_filter = {'date_paiement__range': (today, end_date)}
    else:
        cd_filter = {'date_commande__gte': today}
        traite_filter = {'date_echeance__gte': today}
        salaire_filter = {'date_paiement__gte': today}


    # 1. Upcoming client invoices
    invoices = Cd.objects.filter(
        statut='pending',
        is_deleted=False,
        **cd_filter
    )
    for inv in invoices:
        upcoming_events.append({
            'date': inv.date_commande.isoformat(),
            'description': f"Facture Client {inv.client.nom_client}",
            'amount': inv.montant_ttc,
            'type': 'positive'
        })

    # 2. Upcoming supplier traites
    traites = TraiteFournisseur.objects.filter(
        status='NON_PAYEE',
        plan_traite__is_deleted=False,
        **traite_filter
    )
    for t in traites:
        upcoming_events.append({
            'date': t.date_echeance.isoformat(),
            'description': f"Traite Fournisseur {t.plan_traite.fournisseur.nom}",
            'amount': -t.montant,
            'type': 'supplier'
        })
    
    # 3. Upcoming client traites
    traites = Traite.objects.filter(
        plan_traite__is_deleted=False,
        status='NON_PAYEE',
        **traite_filter
    )
    for t in traites:
        upcoming_events.append({
            'date': t.date_echeance.isoformat(),
            'description': f"Traite Client {t.plan_traite.client.nom_client}",
            'amount': t.montant,
            'type': 'positive'
        })

    # Salaries
    salaries = FichePaie.objects.filter(**salaire_filter)
    for s in salaries:
        upcoming_events.append({
            'date': s.date_paiement.strftime("%Y-%m-%d"),
            'description': f"Salaire employé {s.employe.nom}",
            'amount': -s.net_a_payer,
            'type': 'negative'
        })

    # 4. Sort by date
    upcoming_events.sort(key=lambda x: x['date'])

    return upcoming_events
