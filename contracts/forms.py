from django import forms
from django.forms import formset_factory
from django.utils.translation import gettext_lazy as _
from .models import Trip
from pathlib import Path
from .models import Contract, Trip

class ContractForm(forms.Form):
    trip = forms.ModelChoiceField(queryset=Trip.objects.all(), label=_("Trip"))
    email = forms.EmailField(label=_("Email for sending"))
    price = forms.DecimalField(label=_("Package price (EUR)"), max_digits=10, decimal_places=2)
    deposit = forms.DecimalField(label=_("Deposit (EUR)"), required=False, max_digits=10, decimal_places=2)
    
class TravelerForm(forms.Form):
    full_name = forms.CharField(label=_("Full name"), max_length=200, required=False)
    egn = forms.CharField(label=_("Personal ID (EGN/LNCh)"), max_length=10, required=False)
    
    def clean(self):
        cleaned = super().clean()
        name = cleaned.get("full_name", "").strip()
        egn = cleaned.get("egn", "").strip()
        
        if name and not egn:
            self.add_error("egn", _("Enter the personal ID."))
        if egn and not name:
            self.add_error("full_name", _("Enter the name."))
        if egn and (not egn.isdigit() or len(egn) != 10):
            self.add_error("egn", _("The personal ID must be exactly 10 digits."))
        return cleaned
TravelerFormSet = formset_factory(TravelerForm, extra=4)

ALLOWED_SIGNED_EXTENSIONS = [".pdf", ".jpg", ".jpeg", ".png"]
MAX_SIGNED_SIZE_MB = 10

class SignedContractForm(forms.Form):
    signed_file = forms.FileField(label=_("Signed contract (PDF or photo)"))
    
    def clean_signed_file(self):
        uploaded=self.cleaned_data["signed_file"]
        
        if Path(uploaded.name).suffix.lower() not in ALLOWED_SIGNED_EXTENSIONS:
            raise forms.ValidationError(_("Allowed file types: PDF, JPG, PNG."))
        if uploaded.size > MAX_SIGNED_SIZE_MB * 1024 * 1024:
            raise forms.ValidationError(_("The file is larger than %(size)s MB.") % {"size": MAX_SIGNED_SIZE_MB})
        return uploaded
    
class TripForm(forms.ModelForm):
    class Meta:
        model = Trip
        fields = "__all__"
        widgets = {
            "date_from": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "date_to": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "included": forms.Textarea(attrs={"rows": 2}),
            "not_included": forms.Textarea(attrs={"rows": 2}),
            "cancelation_terms": forms.Textarea(attrs={"rows": 3}),        
        }
        
        def clean(self):
            cleaned = super().clean()
            date_from = cleaned.get("date_from")
            date_to = cleaned.get("date_to")
            if date_from and date_to and date_to < date_from:
                self.add_error("date_to", _("The end date cannot be before the start date."))
                
            return cleaned

class ContractEditForm(forms.ModelForm):
    class Meta:
        model = Contract
        fields = ["contract_date", "trip", "price", "deposit", "email"]
        widgets = {
            "contract_date": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
        }