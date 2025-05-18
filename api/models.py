from django.db import models
import re


def validate_email(value):
    from django.core.exceptions import ValidationError

    email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    if not re.match(email_pattern, value):
        raise ValidationError("Format d'email invalide")


def validate_phone(value):
    from django.core.exceptions import ValidationError

    if not value.isdigit():
        raise ValidationError("Le numéro doit contenir uniquement des chiffres")


class Client(models.Model):
    nom_client = models.CharField(max_length=255, help_text="Client name")
    numero_fiscal = models.CharField(
        max_length=255, unique=True, help_text="Fiscal registration number"
    )
    adresse = models.CharField(
        max_length=255, blank=True, null=True, help_text="Client address"
    )
    telephone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        validators=[validate_phone],
        help_text="Client phone number",
    )
    nom_responsable = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Manager or responsible person's name",
    )
    email = models.EmailField(
        blank=True, null=True, validators=[validate_email], help_text="Client's email"
    )
    email_responsable = models.EmailField(
        blank=True,
        null=True,
        validators=[validate_email],
        help_text="Manager or responsible person's email",
    )
    telephone_responsable = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        validators=[validate_phone],
        help_text="Manager or responsible person's phone number",
    )
    autre_numero = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        validators=[validate_phone],
        help_text="Other optional number",
    )
    informations_complementaires = models.TextField(
        blank=True, null=True, help_text="Additional information about the client"
    )
    date_creation = models.DateTimeField(
        auto_now_add=True, help_text="Date when the client was created"
    )
    derniere_mise_a_jour = models.DateTimeField(
        auto_now=True, help_text="Date when the client was last updated"
    )

    class Meta:
        ordering = ["nom_client"]
        indexes = [
            models.Index(fields=["nom_client"]),
            models.Index(fields=["numero_fiscal"]),
        ]

    def __str__(self):
        return self.nom_client
