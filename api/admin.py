from django.contrib import admin
from .models import Client, Traveaux, Produit, Matiere, MatiereUsage, FactureTravaux, FactureMatiere, PlanTraite, Traite, Entreprise    

admin.site.register(Client)
admin.site.register(Traveaux)
admin.site.register(Produit)
admin.site.register(Matiere)
admin.site.register(MatiereUsage)
admin.site.register(FactureTravaux)
admin.site.register(FactureMatiere)
admin.site.register(PlanTraite)
admin.site.register(Traite)
admin.site.register(Entreprise)
