from django.urls import path
from . import views

app_name = 'qr_code'

urlpatterns = [
    path('generate/<int:album_id>/', views.generate_qr_code, name='generate'),
    path('print/<int:album_id>/', views.print_qr_card, name='print_qr_card'),
]