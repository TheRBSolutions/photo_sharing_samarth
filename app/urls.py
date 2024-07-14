# gallery/urls.py
from django.urls import path
from . import views

from django.contrib.auth import views as auth_views


urlpatterns = [
    # path('', views.home, name='home'),
    # path('upload/', views.upload_photos, name='upload_photos'),
    path('signup/', views.RegisterPage, name='register'),
    path('login/', views.loginPage, name='login'),
    path('logout/', views.logoutUser, name="logout"),
    path('dashboard/', views.photographer_dashboard, name='photographer_dashboard'),
     path('create_album/', views.create_album, name='create_album'),
    path('album/<int:id>/', views.album_detail, name='album_detail'),
    path('album/<int:id>/upload_selfie/', views.upload_selfie, name='upload_selfie'),
    path('album_settings/<int:id>/', views.album_settings, name='album_settings'),
    path('sharable/album/<int:id>/', views.shared_album_detail, name='shared_album_detail'),
    # path('event/<int:event_id>/', views.view_photos, name='view_photos'),
    path('upgrade_subscription/', views.upgrade_subscription, name='upgrade_subscription'),
    path('photographer_settings/', views.photographer_settings, name='photographer_settings'),
    
    path('delete_image/', views.delete_image, name='delete_image'),
    path('delete_all_images/', views.delete_all_images, name='delete_all_images'),
    path('business_settings/', views.business_settings, name='business_settings'),
     
        path('reset_password/',
     auth_views.PasswordResetView.as_view(template_name="app/password_reset.html"),
     name="reset_password"),

    path('reset_password_sent/', 
        auth_views.PasswordResetDoneView.as_view(template_name="app/password_reset_sent.html"), 
        name="password_reset_done"),

    path('reset/<uidb64>/<token>/',
     auth_views.PasswordResetConfirmView.as_view(template_name="app/password_reset_form.html"), 
     name="password_reset_confirm"),

    path('reset_password_complete/', 
        auth_views.PasswordResetCompleteView.as_view(template_name="app/password_reset_done.html"), 
        name="password_reset_complete"),
    
    
    
     path('upload-images/<int:album_id>/', views.upload_images, name='upload_images'),
]


