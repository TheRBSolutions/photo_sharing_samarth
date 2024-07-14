#  mypy: ignore-missing-imports
from django.db import models


from django.contrib.auth.models import User


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    is_photographer = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username # pylint: disable=no-member


class Business(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20)
    email = models.EmailField()
    website = models.URLField(blank=True, null=True)
    social_media_links = models.TextField(
        blank=True, null=True, help_text="Enter social media links separated by commas"
    )
    logo = models.ImageField(upload_to="business_logos/", default="business_logos/default/ball.jpg", blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.name and self.user:
            # pylint: disable=no-member
            self.name = self.user.username # pylint: disable=no-member
        super().save(*args, **kwargs)
        
    def __str__(self):
        return self.name
    


class StorageDetails(models.Model):
    profile = models.OneToOneField(
        Profile, on_delete=models.CASCADE, related_name="storage"
    )
    total_uploads = models.IntegerField(default=0)
    storage_used = models.FloatField(default=0.0)  # in MB or GB
    total_albums = models.IntegerField(default=0)
    # upload_limit = models.IntegerField(default=0)
    # pylint: disable=no-member
    def __str__(self):
        return f"Storage details for {self.profile.user.username}"

    def update_storage(self, bucket_name):
        prefix = f"index_gallery/{self.profile.user.username}/"
        new_storage_used, new_total_uploads = get_total_storage_and_uploads(
            bucket_name, prefix
        )
        self.storage_used = new_storage_used
        self.total_uploads = new_total_uploads
        self.save()
    # pylint: disable=no-member

import boto3
from botocore.config import Config

session = boto3.Session()
s3_client = session.client("s3", config=Config(signature_version="s3v4"), verify=False)


def get_total_storage_and_uploads(bucket_name, prefix):
    total_size = 0
    total_uploads = 0
    try:
        response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
        print(response)
        if "Contents" in response:
            total_uploads = len(response["Contents"])
            for obj in response["Contents"]:
                total_size += obj["Size"]
    except Exception as e:
        print(f"Error fetching storage details: {e}")
    return total_size / (1024 * 1024), total_uploads  # Convert to MB


class Subscription(models.Model):
    PLAN_CHOICES = (
        ("Free", "Free"),
        ("Basic", "Basic"),
        ("Premium", "Premium"),
    )

    profile = models.OneToOneField(
        Profile, on_delete=models.CASCADE, related_name="subscription"
    )
    plan = models.CharField(max_length=20, choices=PLAN_CHOICES, default="Free")
    start_date = models.DateField(auto_now_add=True)
    end_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.profile.user.username} - {self.plan} Plan"


class Album(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    photographer = models.ForeignKey(User, on_delete=models.CASCADE)
    cover_image = models.ImageField(
        upload_to="album_covers/",
        default="images/Wedding-Album-Cover-Design-PSD-08.jpg",
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.title)


class Media(models.Model):
    album = models.ForeignKey(Album, on_delete=models.CASCADE)
    file = models.FileField(upload_to="media/")
    folder_name = models.CharField(max_length=255, blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.album.title} - {self.folder_name or 'No Folder'}"


class UserProfile(models.Model):
    email = models.EmailField(unique=False, blank=True, null=True)
    selfie = models.ImageField(upload_to="user_selfies/")
    user_for_album = models.ForeignKey(
        Album, on_delete=models.CASCADE, blank=True, null=True
    )
    encoded_face = models.TextField(blank=True, null=True)  # To store the encoded face


class AdminUserSettings(models.Model):
    DATE_FORMATS = (
        ("d-m-Y", "d-m-Y"),
        ("m-d-Y", "m-d-Y"),
        ("Y-m-d", "Y-m-d"),
        ("m/d/Y", "m/d/Y"),
        ("d/m/Y", "d/m/Y"),
        ("Y/m/d", "Y/m/d"),
        ("m.d.Y", "m.d.Y"),
        ("d.m.Y", "d.m.Y"),
        ("Y.m.d", "Y.m.d"),
        ("d M Y", "d M Y"),
    )

    CURRENCY_FORMATS = (
        ("$", "USD - United States Dollar"),
        ("€", "EUR - Euro"),
        ("¥", "JPY - Japanese Yen"),
        ("£", "GBP - British Pound"),
        ("A$", "AUD - Australian Dollar"),
        ("C$", "CAD - Canadian Dollar"),
        ("CHF", "CHF - Swiss Franc"),
        ("¥", "CNY - Chinese Yuan"),
        ("kr", "SEK - Swedish Krona"),
        ("NZ$", "NZD - New Zealand Dollar"),
        ("₹", "INR - Indian Rupee"),
        ("R$", "BRL - Brazilian Real"),
        ("R", "ZAR - South African Rand"),
        ("₽", "RUB - Russian Ruble"),
        ("₩", "KRW - South Korean Won"),
        ("S$", "SGD - Singapore Dollar"),
        ("$", "MXN - Mexican Peso"),
        ("Rp", "IDR - Indonesian Rupiah"),
        ("₺", "TRY - Turkish Lira"),
        ("﷼", "SAR - Saudi Riyal"),
        ("kr", "NOK - Norwegian Krone"),
        ("zł", "PLN - Polish Zloty"),
        ("฿", "THB - Thai Baht"),
        ("RM", "MYR - Malaysian Ringgit"),
        ("₫", "VND - Vietnamese Dong"),
    )

    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, null=False, blank=False, on_delete=models.CASCADE)
    app_name = models.CharField(
        max_length=200, null=True, blank=True, default="Recursion Club"
    )
    company_name = models.CharField(
        max_length=200, null=True, blank=True, default="Recursion Club"
    )
    company_phone = models.CharField(max_length=200, null=True, blank=True)
    date_format = models.CharField(
        max_length=200, null=True, default="d M Y", blank=True, choices=DATE_FORMATS
    )
    currency = models.CharField(
        max_length=200,
        null=True,
        default="INR - Indian Rupee",
        blank=True,
        choices=CURRENCY_FORMATS,
    )
    company_address = models.CharField(max_length=400, null=True, blank=True)
    company_logo_url = models.CharField(max_length=200, null=True, blank=True)
    generate_invoice_email_before_x_days = models.IntegerField(
        default=1, null=False, blank=False
    )
    app_logo = models.ImageField(default="logo.png", null=True, blank=True)
    favicon = models.ImageField(default="profile1.png", null=True, blank=True)
    is_whatsapp_service_active = models.BooleanField(
        blank=True, null=True, default=True
    )
    is_money_paid = models.BooleanField(blank=True, null=True, default=True)

    def __str__(self):
        return f"{self.user.username}-{str(self.id)}"
