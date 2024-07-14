import qrcode
import io
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from app.models import Album, Profile ,Business # Import Album from the original app

def generate_qr_code(request, album_id):
    album = get_object_or_404(Album, id=album_id)
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr_data = f"https://samarth1011.pythonanywhere.com/album/{album_id}/upload_selfie/"
    qr.add_data(qr_data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return HttpResponse(buffer, content_type="image/png")

def print_qr_card(request, album_id):
    album = get_object_or_404(Album, id=album_id)
    user_profile = get_object_or_404(Profile, user=request.user)
    business = get_object_or_404(Business, user=album.photographer)
    return render(
        request, "qr_code/print_qr_card.html", {"album": album, "profile": user_profile, "business": business}
    )