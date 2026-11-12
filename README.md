# Enev Contract

A web application for a Bulgarian tour operator (ENEV HOLIDAY) that automates the
full lifecycle of travel package contracts — from data entry to a signed, archived contract.

## The problem

Contracts were prepared by hand in a Word file for every traveler: copying names,
personal IDs, trip details and prices, numbering them manually and tracking by memory
which ones were sent and signed.

## The solution

1. Enter the trip once and the travelers for each contract.
2. **Create contract** – the system assigns the next contract number automatically.
3. **Generate PDF** – the full legal contract in Bulgarian with all data filled in.
4. **Send by email** – the PDF goes to the client as an attachment.
5. **Upload the signed copy** – the client signs and returns it; it is stored with the contract.
6. **Archive** – every contract has a clear status: Draft → Sent → Signed → Archived (or Cancelled).

## Features

- Automatic contract numbering
- PDF generation with Cyrillic fonts (xhtml2pdf + DejaVu Sans)
- Email sending with the PDF attached
- Upload of the signed contract (PDF/JPG/PNG, validated type and size)
- Status tracking and search by number, name, personal ID or destination
- Trip management with a "copy trip" shortcut for recurring tours
- Bilingual interface: Bulgarian and English (Django i18n)
- Personal data protection: all pages and files require login; uploaded files are never public

## Screenshots

| Contracts | Contract details |
|---|---|
| ![Contracts](docs/screenshots/contracts.png) | ![Details](docs/screenshots/detail.png) |

| New contract | Generated PDF |
|---|---|
| ![New contract](docs/screenshots/new_contract.png) | ![PDF](docs/screenshots/pdf.png) |

## Tech stack

- **Python 3.13+ / Django 6.1** – models, forms, formsets, class-free function views
- **SQLite** – database
- **xhtml2pdf** – HTML → PDF
- **Pico CSS** – responsive layout
- **Deployment:** PythonAnywhere (HTTPS, environment variables for secrets)

## Run locally

```bash
git clone https://github.com/viktoryia-eneva/Enev-Contract.git
cd Enev-Contract
python -m venv venv
venv\Scripts\activate        # Windows  (Linux/macOS: source venv/bin/activate)
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open http://127.0.0.1:8000 and log in. Without email settings, emails are printed in the terminal.

Optional `.env` file for real email sending:

```
EMAIL_USER=your@gmail.com
EMAIL_PASSWORD='gmail-app-password'
```

## What I learned

- Modelling a real business process with Django models, relations and statuses
- Generating documents (PDF) from templates
- Handling file uploads and keeping personal data private
- Internationalization (i18n) of a Django project
- Deploying a Django app and managing secrets with environment variables