from django.urls import path

from . import views
app_name = "contracts"

urlpatterns = [path("", views.contract_list, name="list"),
               path("new/", views.contract_create, name="create"),
               path("<int:pk>/", views.contract_detail, name="detail"),
               path("<int:pk>/pdf/", views.contract_pdf, name="pdf"),
               path("<int:pk>/send/", views.contract_send, name="send"),
               path("<int:pk>/upload-signed/", views.contract_upload_signed, name="upload_signed"),
               path("<int:pk>/signed-file/", views.contract_signed_file, name="signed_file"),
               path("<int:pk>/archive/", views.contract_archive, name="archive"),
               path("<int:pk>/cancel/", views.contract_cancel, name="cancel"),
               path("<int:pk>/edit/", views.contract_edit, name="edit"),
               path("trips/", views.trip_list, name="trip_list"),
               path("trips/new/", views.trip_form, name="trip_create"),
               path("trips/<int:pk>/edit/", views.trip_form, name="trip_edit"),
               ]