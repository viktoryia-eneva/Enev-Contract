from django.contrib import admin
from .models import Contract, Traveler, Trip

@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    list_display = ("destination", "date_from", "date_to", "price")
    serach_fileds = ("destination")

@admin.register(Traveler)
class TravelerAdmin(admin.ModelAdmin):
    list_display = ("full_name", "egn", "email", "phone")
    serach_fileds = ("full_name", "egn", "email")
    
@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = ("number", "contract_date", "trip", "status")
    list_filter = ("status", "trip")
    search_fields = ("number", "travelers__full_name", "travelers__egn")
    filter_horizontal = ("travelers",)
    fields = ("number", "contract_date", "trip", "travelers", "deposit", "status")
    readonly_fields = ("number", "status")