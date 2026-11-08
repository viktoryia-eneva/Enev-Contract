from django.db import models
from datetime import date
from django.db.models import Max
from django.utils.translation import gettext_lazy as _

FIRST_CONTRACT_NUMBER = 177

class trip(models.Model):
    destinantion = models.CharField(_("Destination"), max_length=200)
    date_from = models.DateField(_("Date from"))
    date_to = models.DateField(_("Date to"))
    start_point = models.CharField(_("Departure point"), max_length=200)
    end_point = models.CharField(_("Return point"), max_length=200)
    transport = models.CharField(_("Transport"), max_length=100, default="автобус")
    accommodation = models.CharField(_("Accommodation"), max_length=200, default="да")
    night = models.CharField(_("Overnight stays"), max_length=200, default="да")
    meals = models.CharField(_("Meals"), max_length=200, blank=True)
    price = models.DecimalField(_("Price (EUR)"), max_digits=10, decimal_places=2)
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
        ordering = ["-data_from"]
    
    def __str__(self):
        return f"{self.destinantion} ({self.date_from:%d.%m.%Y} - {self.date_to:%d.%m.%Y})"
    
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
            