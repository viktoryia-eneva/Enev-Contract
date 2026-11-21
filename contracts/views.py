from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext as _

from .forms import ContractForm, TravelerFormSet
from .models import Contract, Traveler, Trip
from django.http import HttpResponse
from .pdf import render_contract_pdf
from urllib.parse import quote
from django.core import signing
from django.urls import reverse

import smtplib

from django.contrib import messages
from django.views.decorators.http import require_POST
from .emails import send_cancellation_email, send_contract_email
from pathlib import Path
from django.db.models import Q, Count
from django.http import FileResponse, Http404, HttpResponse
from django.utils import timezone
from .forms import ContractForm,ContractEditForm, SignedContractForm, TravelerFormSet, TripForm
from django.forms import model_to_dict

def calculate_price(trip, traveler_count):
    """Total price = price per person x number of travelers."""
    
    return trip.price_per_person * traveler_count

SHARE_SALT = 'contract-share'
SHARE_DAYS = 7

def make_share_url(request, contract):
    """Signed link to the contract PDF that works without login."""
    token = signing.dumps(contract.pk, salt=SHARE_SALT)
    return request.build_absolute_uri(reverse("contracts:public_pdf", args=[token]))

def save_travelers(rows):
    """Create or update travelers by EGN and return the list."""
    travelers = []
    for row in rows:
        traveler, _created = Traveler.objects.update_or_create(egn=row["egn"].strip(),defaults={"full_name": row["full_name"].strip()},
                                                               )
        travelers.append(traveler)
    return travelers

@login_required
def contract_list(request):
    contracts = Contract.objects.select_related("trip").prefetch_related("travelers")
    
    status = request.GET.get("status", "")
    query = request.GET.get("q", "").strip()
    
    if status:
        contracts = contracts.filter(status=status)
    if query:
        filters = (
            Q(travelers__full_name__icontains=query)
            | Q(travelers__egn__icontains=query)
            | Q(trip__destination__icontains=query)
            | Q(email__icontains=query)
        )
        if query.isdigit():
            filters |= Q(number=int(query))
        contracts = contracts.filter(filters).distinct()
    
    return render(request,
                  "contracts/contract_list.html", {
                      "contracts": contracts,
                      "statuses": Contract.Status.choices,
                      "current_status": status,
                      "query": query,
                  })

@login_required
def contract_create(request):
    if request.method == "POST":
        form = ContractForm(request.POST)
        formset = TravelerFormSet(request.POST, prefix="travelers")
        
        if form.is_valid() and formset.is_valid():
            rows = [f.cleaned_data for f in formset if f.cleaned_data.get("egn")]
            
            if not rows:
                form.add_error(None, _("Add at least one traveler."))
            else:
                with transaction.atomic():
                    contract = Contract.objects.create(
                        trip = form.cleaned_data["trip"],
                        
                        email = form.cleaned_data["email"],
                        price = form.cleaned_data["price"] if form.cleaned_data["price"] is not None
                        else calculate_price(form.cleaned_data["trip"], len(rows)),
                        deposit = form.cleaned_data["deposit"],
                    )
                    
                    contract.travelers.set(save_travelers(rows))
                return redirect("contracts:detail", pk=contract.pk)
    else:
        form = ContractForm()
        formset = TravelerFormSet(prefix="travelers")
    
    return render(request, "contracts/contract_form.html", {"form": form, "formset": formset})

@login_required
def contract_detail(request, pk):
    contract = get_object_or_404(Contract.objects.select_related("trip"), pk=pk)
    share_url = make_share_url(request, contract)
    text = (f"Здравейте, изпращаме Ви договор № {contract.number} за екскурзия "
            f"„{contract.trip.destination}“: {share_url} (линкът е валиден {SHARE_DAYS} дни)")
    
    return render(request, "contracts/contract_detail.html", {"contract": contract, "upload_form": SignedContractForm(), "share_url": share_url, "whatsapp_url": "https://wa.me/?text=" + quote(text),"viber_url":"viber://forward?text=" + quote(text), })


@login_required
def contract_pdf(request, pk):
    contract = get_object_or_404(Contract.objects.select_related("trip"), pk=pk)
    pdf_bytes = render_contract_pdf(contract)
    
    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = f'inline;filename="contract_{contract.number}.pdf"'
    return response

def contract_public_pdf(request, token):
    """PDF for the client via a signed link - no login, expires after SHARE_DAYS."""
    try:
        pk = signing.loads(token, salt = SHARE_SALT, max_age=SHARE_DAYS * 24 * 60 * 60)
    except signing.BadSignature:
        raise Http404
    contract = get_object_or_404(Contract.objects.select_related("trip"), pk=pk)
    if contract.status == Contract.Status.CANCELLED: 
        raise Http404
    
    response = HttpResponse(render_contract_pdf(contract), content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="contract_{contract.number}.pdf"'
    return response

@login_required
@require_POST
def contract_send(request, pk):
    contract = get_object_or_404(Contract.objects.select_related("trip"), pk=pk)
    
    if  contract.is_closed():
        messages.error(request, _("Archived or cancelled contracts cannot be sent."))
        return redirect("contracts:detail", pk=pk)
    
    if not contract.email:
        messages.error(request, _("This contract has no email address."))
        return redirect("contracts:detail", pk=pk)
    
    try:
        send_contract_email(contract)
    except (smtplib.SMTPException, OSError) as error:
        messages.error(request, _("Sending failed: %(error)s") % {"error": error})
    else:
        messages.success(request, _("The contract was sent to %(email)s.") % {"email": ",".join(contract.email_list())})
    return redirect("contracts:detail", pk=pk)

@login_required
@require_POST
def contract_upload_signed(request, pk):
    contract = get_object_or_404(Contract, pk=pk)
    form = SignedContractForm(request.POST, request.FILES)
    
    if form.is_valid():
        uploaded = form.cleaned_data["signed_file"]
        extension = Path(uploaded.name).suffix.lower()
        
        if contract.signed_file:
            contract.signed_file.delete(save=False)
        contract.signed_file.save(f"contract_{contract.number}_signed{extension}", uploaded, save=False)
        contract.status = Contract.Status.SIGNED
        contract.signed_at= timezone.now()
        contract.save()
        messages.success(request, _("The signed contract was uploaded."))
    else:
        for error in form.errors.get("signed_file", []):
            messages.error(request, error)
    return redirect("contracts:detail", pk=pk)

@login_required
def contract_signed_file(request, pk):
    contract = get_object_or_404(Contract, pk=pk)
    if not contract.signed_file:
        raise Http404
    return FileResponse(
        contract.signed_file.open("rb"),
        filename=Path(contract.signed_file.name).name,
    )
    
@login_required
@require_POST
def contract_archive(request, pk):
    contract = get_object_or_404(Contract, pk=pk)
    if contract.can_archive():
        contract.status = Contract.Status.ARCHIVED
        contract.save(update_fields=["status", "updated_at"])
        messages.success(request, _("The contract was archived."))
    return redirect("contracts:detail", pk=pk)

@login_required
@require_POST
def contract_cancel(request, pk):
    contract = get_object_or_404(Contract.objects.select_related("trip"), pk=pk)
    if contract.can_cancel():
        contract.status = Contract.Status.CANCELLED
        contract.save(update_fields=["status", "updated_at"])
        messages.success(request, _("The contract was cancelled."))
        
        if contract.email_list():
            try:
                send_cancellation_email(contract)
            except (smtplib.SMTPException, OSError) as error:
                messages.warning(request, _("The client was not notified: %(error)s") % {"error": error})
            else:
                messages.info(request, _("The client was notified by email."))
    return redirect("contracts:detail", pk=pk)

@login_required
@require_POST
def contract_delete(request, pk):
    contract = get_object_or_404(Contract, pk=pk)
    number = contract.number
    
    if contract.pdf:
        contract.pdf.delete(save=False)
    if contract.signed_file:
        contract.signed_file.delete(save=False)
    
    contract.delete()
    messages.success(request, _("Contract № %(number)s was deleted.") % {"number": number})
    return redirect("contracts:list")

@login_required
def trip_list(request):
    trips = Trip.objects.annotate(contract_count=Count("contracts"))
    return render(request, "contracts/trip_list.html", {"trips": trips})

@login_required
def trip_form(request, pk=None):
    """One view for both creating (no pk) and editing (with pk) a trip."""
    trip = get_object_or_404(Trip, pk=pk) if pk else None
    
    initial = None
    copy_id = request.GET.get("copy")
    if trip is None and copy_id:
        source = get_object_or_404(Trip, pk=copy_id)
        initial = model_to_dict(source, exclude=["id"])
        
    form = TripForm(request.POST or None, instance=trip, initial=initial)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, _("The trip was saved."))
        return redirect("contracts:trip_list")
    return render(request, "contracts/trip_form.html", {"form": form, "trip": trip})

@login_required
def contract_edit(request, pk):
    contract = get_object_or_404(Contract, pk=pk)
    if contract.is_closed():
        messages.error(request, _("Archived or cancelled contracts cannot be edited."))
        return redirect("contracts:detail", pk=pk)
    
    initial = [{"full_name": t.full_name, "egn": t.egn} for t in contract.travelers.all()]
    form = ContractEditForm(request.POST or None, instance=contract)
    formset = TravelerFormSet(request.POST or None, prefix="travelers", initial=initial)
    
    if request.method == "POST" and form.is_valid() and formset.is_valid():
        rows = [f.cleaned_data for f in formset if f.cleaned_data.get("egn")]
        if not rows:
            form.add_error(None, _("Add at least one traveler."))
        else:
            with transaction.atomic():
                contract = form.save(commit=False)
                if form.cleaned_data["price"] is None:
                    contract.price = calculate_price(contract.trip, len(rows))
                contract.save()
                contract.travelers.set(save_travelers(rows))
            messages.success(request, _("The contract was saved."))
            return redirect("contracts:detail", pk=pk)

    return render(request, "contracts/contract_edit.html",
                  {"form": form, "formset": formset, "contract": contract})
       