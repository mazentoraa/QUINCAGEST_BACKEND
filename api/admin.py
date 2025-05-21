from django.contrib import admin
from .models import Client, Traveaux, Produit, Matiere, MatiereUsage, FactureTravaux, FactureMatiere

admin.site.register(Client)
admin.site.register(Traveaux)
admin.site.register(Produit)
admin.site.register(Matiere)
admin.site.register(MatiereUsage)
admin.site.register(FactureTravaux)
admin.site.register(FactureMatiere)
