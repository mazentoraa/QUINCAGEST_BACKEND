from .models import Avance, Remboursement
from django.utils import timezone

def appliquer_remboursement_avance(fiche_paie):
    employe = fiche_paie.employe
    total_deduction = 0

    avances = Avance.objects.filter(employee=employe, statut='Acceptée')

    for avance in avances:
        reste = avance.reste()
        if reste > 0:
            mensualite = avance.mensualite()
            montant = min(mensualite, reste)

            Remboursement.objects.create(
                avance=avance,
                date=fiche_paie.date_creation.date(),
                montant=montant
            )

            total_deduction += montant

    fiche_paie.avance_deduite = total_deduction
    fiche_paie.net_a_payer = max(fiche_paie.net_a_payer - total_deduction, 0)
    fiche_paie.save()
