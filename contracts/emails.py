from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.utils import timezone, translation

from .models import Contract
from .pdf import render_contract_pdf


def send_contract_email(contract):
    """Generate a fresh PDF, email it to the client and mark the contract as sent."""
    pdf_bytes = render_contract_pdf(contract)

    with translation.override("bg"):
        body = render_to_string(
            "contracts/email_contract.txt",
            {"contract": contract, "trip": contract.trip},
        )

    message = EmailMessage(
        subject=f"Договор № {contract.number} – {contract.trip.destination}",
        body=body,
        to=[contract.email],
    )
    message.attach(f"contract_{contract.number}.pdf", pdf_bytes, "application/pdf")
    message.send()

    # Only reached if sending succeeded (otherwise send() raises an error)
    contract.status = Contract.Status.SENT
    contract.sent_at = timezone.now()
    contract.save(update_fields=["status", "sent_at", "updated_at"])