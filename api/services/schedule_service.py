from datetime import date
from django.utils.timezone import now
from api.models import Cd, TraiteFournisseur


def get_schedule():
    today = date.today()
    upcoming_events = []

    # 1. Upcoming client invoices
    invoices = Cd.objects.filter(
        statut='pending',
        date_commande__gte=today
    )
    for inv in invoices:
        upcoming_events.append({
            'date': inv.date_commande.isoformat(),
            'description': f"Encaissement {inv.client.nom_client}",
            'amount': inv.montant_ttc,
            'type': 'positive'
        })

    # 2. Upcoming supplier traites
    traites = TraiteFournisseur.objects.filter(
        status='NON_PAYEE',
        date_echeance__gte=today
    )
    for t in traites:
        upcoming_events.append({
            'date': t.date_echeance.isoformat(),
            'description': f"Traite {t.plan_traite.fournisseur.nom}",
            'amount': -t.montant,
            'type': 'supplier'
        })

    # salaries (After finishing module employé)
    # salaries = Salary.objects.filter(date__gte=today)
    # for s in salaries:
    #     upcoming_events.append({
    #         'date': s.date.isoformat(),
    #         'description': "Salaire employé",
    #         'amount': -s.amount,
    #         'type': 'negative'
    #     })

    # 4. Sort by date
    upcoming_events.sort(key=lambda x: x['date'])

    return upcoming_events
