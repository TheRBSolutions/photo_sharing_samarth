from django.contrib import admin # type: ignore
from .models import *
# Register your models here.

admin.site.register(UserProfile)

admin.site.register(Profile)

admin.site.register(Media)
admin.site.register(Album)

admin.site.register(StorageDetails)
admin.site.register(Subscription)
admin.site.register(Business)
