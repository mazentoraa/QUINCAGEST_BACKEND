from django.db import migrations, models

def generate_client_codes(apps, schema_editor):
        Client = apps.get_model('api', 'Client')
        for client in Client.objects.all():
            client.code_client = f"{client.id:05d}"
            client.save()

class Migration(migrations.Migration):

    dependencies = [
        ('api', '0034_alter_produit_epaisseur_alter_produit_largeur_and_more'),
    ]
   

    operations = [
        migrations.AddField(
            model_name='bonretour',
            name='deleted_at',
            field=models.DateTimeField(blank=True, help_text='Date when the BON was returned', null=True),
        ),
        migrations.AddField(
            model_name='bonretour',
            name='is_deleted',
            field=models.BooleanField(default=False, help_text='BON returned'),
        ),
        migrations.AddField(
            model_name='client',
            name='code_client',
            field=models.CharField(blank=True, max_length=5, null=True),
        ),
        migrations.AddField(
            model_name='client',
            name='deleted_at',
            field=models.DateTimeField(blank=True, help_text='Date when the client was deleted', null=True),
        ),
        migrations.AddField(
            model_name='client',
            name='is_deleted',
            field=models.BooleanField(default=False, help_text='Client deleted'),
        ),
        migrations.AddField(
            model_name='commande',
            name='deleted_at',
            field=models.DateTimeField(blank=True, help_text='Date when the order was deleted', null=True),
        ),
        migrations.AddField(
            model_name='commande',
            name='is_deleted',
            field=models.BooleanField(default=False, help_text='Order deleted'),
        ),
        migrations.AddField(
            model_name='commandeproduit',
            name='deleted_at',
            field=models.DateTimeField(blank=True, help_text='Date when the tax was deleted', null=True),
        ),
        migrations.AddField(
            model_name='commandeproduit',
            name='is_deleted',
            field=models.BooleanField(default=False, help_text='Tax deleted'),
        ),
        migrations.AddField(
            model_name='devis',
            name='deleted_at',
            field=models.DateTimeField(blank=True, help_text='Date when the quote was deleted', null=True),
        ),
        migrations.AddField(
            model_name='devis',
            name='is_deleted',
            field=models.BooleanField(default=False, help_text='Quote deleted'),
        ),
        migrations.AddField(
            model_name='facture',
            name='deleted_at',
            field=models.DateTimeField(blank=True, help_text='Date when the invoice was deleted', null=True),
        ),
        migrations.AddField(
            model_name='facture',
            name='is_deleted',
            field=models.BooleanField(default=False, help_text='Invoice deleted'),
        ),
        migrations.AddField(
            model_name='facturematiere',
            name='deleted_at',
            field=models.DateTimeField(blank=True, help_text='Date when the BON was deleted', null=True),
        ),
        migrations.AddField(
            model_name='facturematiere',
            name='is_deleted',
            field=models.BooleanField(default=False, help_text='BON deleted'),
        ),
        migrations.AddField(
            model_name='facturetravaux',
            name='deleted_at',
            field=models.DateTimeField(blank=True, help_text='Date when the invoice was deleted', null=True),
        ),
        migrations.AddField(
            model_name='facturetravaux',
            name='is_deleted',
            field=models.BooleanField(default=False, help_text='Invoice deleted'),
        ),
        migrations.AddField(
            model_name='matiere',
            name='deleted_at',
            field=models.DateTimeField(blank=True, help_text='Date when the material was deleted', null=True),
        ),
        migrations.AddField(
            model_name='matiere',
            name='is_deleted',
            field=models.BooleanField(default=False, help_text='Material deleted'),
        ),
        migrations.AddField(
            model_name='matiereretour',
            name='deleted_at',
            field=models.DateTimeField(blank=True, help_text='Date when the material was returned', null=True),
        ),
        migrations.AddField(
            model_name='matiereretour',
            name='is_deleted',
            field=models.BooleanField(default=False, help_text='Material returned'),
        ),
        migrations.AddField(
            model_name='matiereusage',
            name='deleted_at',
            field=models.DateTimeField(blank=True, help_text='Date when the material usage was deleted', null=True),
        ),
        migrations.AddField(
            model_name='matiereusage',
            name='is_deleted',
            field=models.BooleanField(default=False, help_text='Material usage deleted'),
        ),
        migrations.AddField(
            model_name='produit',
            name='deleted_at',
            field=models.DateTimeField(blank=True, help_text='Date when the product was deleted', null=True),
        ),
        migrations.AddField(
            model_name='produit',
            name='is_deleted',
            field=models.BooleanField(default=False, help_text='Product deleted'),
        ),
        migrations.AddField(
            model_name='produitcommande',
            name='deleted_at',
            field=models.DateTimeField(blank=True, help_text='Date when the product command was deleted', null=True),
        ),
        migrations.AddField(
            model_name='produitcommande',
            name='is_deleted',
            field=models.BooleanField(default=False, help_text='Product command deleted'),
        ),
        migrations.AddField(
            model_name='produitdevis',
            name='deleted_at',
            field=models.DateTimeField(blank=True, help_text='Date when the product command was deleted', null=True),
        ),
        migrations.AddField(
            model_name='produitdevis',
            name='is_deleted',
            field=models.BooleanField(default=False, help_text='Product command deleted'),
        ),
        migrations.AddField(
            model_name='traveaux',
            name='deleted_at',
            field=models.DateTimeField(blank=True, help_text='Date when the work was deleted', null=True),
        ),
        migrations.AddField(
            model_name='traveaux',
            name='is_deleted',
            field=models.BooleanField(default=False, help_text='Work deleted'),
        ),
        migrations.RunPython(generate_client_codes),
          migrations.AlterField(
            model_name='client',
            name='code_client',
            field=models.CharField(max_length=5, unique=True),
        )
    ]