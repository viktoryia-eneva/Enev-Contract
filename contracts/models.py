from django.db import models
from datetime import date
from django.db.models import Max
from django.utils.translation import gettext_lazy as _

FIRST_CONTRACT_NUMBER = 177

class Trip(models.Model):
    destination = models.CharField(_("Destination"), max_length=200)
    date_from = models.DateField(_("Date from"))
    date_to = models.DateField(_("Date to"))
    start_point = models.CharField(_("Departure point"), max_length=200)
    end_point = models.CharField(_("Return point"), max_length=200)
    transport = models.CharField(_("Transport"), max_length=100, default="автобус")
    accommodation = models.CharField(_("Accommodation"), max_length=200, default="да")
    nights = models.CharField(_("Overnight stays"), max_length=200, default="да")
    meals = models.CharField(_("Meals"), max_length=200, blank=True)
    min_participants = models.PositiveIntegerField(_("Minimum participants"), default=20)
    notice_days = models.PositiveIntegerField(_("Notice period if minimum not reached (working days)"), default=10)
    payment_days = models.PositiveIntegerField(_("Payment deadline (working days before departure)"), default=10)
    included = models.TextField(_("Included services"), blank=True)
    not_included = models.TextField(_("Not included"), blank=True)
    documents_required = models.CharField(_("Passport/visa/health requirements"), max_length=200, default="не")
    cancellation_terms = models.TextField(_("Cancellation terms"), blank=True)
    
    class Meta:
        verbose_name = _("Trip")
        verbose_name_plural = _("Trips")
        ordering = ["-date_from"]
    
    def __str__(self):
        return f"{self.destination} ({self.date_from:%d.%m.%Y} - {self.date_to:%d.%m.%Y})"
    
class Traveler(models.Model):
        full_name = models.CharField(_("Full name"), max_length=200)
        egn = models.CharField(_("Personal ID (EGN/LNCh)"), max_length=10, unique=True)
        email = models.EmailField(_("Email"), blank=True)
        phone = models.CharField(_("Phone"), max_length=30, blank=True)
        
        class Meta:
            verbose_name = _("Traveler")
            verbose_name_plural = _("Travelers")
            ordering = ["full_name"]
        
        def __str__(self):
            return self.full_name
    
class Contract(models.Model):
        class Status(models.TextChoices):
            DRAFT = "draft", _("Draft")
            SENT = "sent", _("Sent")
            SIGNED = "signed", _("Signed")
            ARCHIVED = "archived", _("Archived")
            CANCELLED = "cancelled", _("Canceled")
            
        number = models.PositiveIntegerField(_("Number"), unique = True, blank=True)
        contract_date = models.DateField(_("Contract date"), default=date.today)
        trip = models.ForeignKey(Trip, on_delete=models.PROTECT, related_name="contracts", verbose_name=_("Trip"))
        travelers = models.ManyToManyField(Traveler, related_name="contracts", verbose_name=_("Travelers"))
        price = models.DecimalField(_("Package price (EUR)"), max_digits=10, decimal_places=2, default=0)
        deposit = models.DecimalField(_("Deposit (EUR)"), max_digits=10, decimal_places=2, null=True, blank=True)
        email = models.EmailField(_("Email for sending"), blank=True)
        status = models.CharField(_("Status"), max_length=20, choices=Status.choices, default=Status.DRAFT)
        pdf = models.FileField(_("Generated PDF"), upload_to="contracts/generated/", blank=True)
        signed_file = models.FileField(_("Signed contract"), upload_to="contracts/signed/", blank=True)
        sent_at = models.DateTimeField(_("Sent at"), null=True, blank=True)
        signed_at = models.DateTimeField(_("Signed at"), null=True, blank=True)
        created_at = models.DateTimeField(_("Created at"), auto_now_add=True)
        updated_at = models.DateTimeField(_("Updated at"), auto_now=True)
        
        class Meta:
            verbose_name = _("Contract")
            verbose_name_plural = _("Contracts")
            ordering = ["-number"]
        
        def __str__(self):
            return f"№ {self.number} / {self.contract_date:%d.%m.%Y}"
        
        def can_archive(self):
            return self.status == self.Status.SIGNED
        
        def can_cancel(self):
            return self.status in (self.Status.DRAFT, self.Status.SENT, self.Status.SIGNED)
        
        def is_closed(self):
            return self.status in (self.Status.ARCHIVED, self.Status.CANCELLED)
        
        def save(self, *args, **kwargs):
            if not self.number:
                last = Contract.objects.aggregate(Max("number"))["number__max"]
                self.number = (last or FIRST_CONTRACT_NUMBER - 1) + 1 
            super().save(*args, **kwargs)