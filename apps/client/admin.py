from django.contrib import admin

from apps.client.models import Contact, Organisation

# Register your models here.
admin.site.register(Organisation)
admin.site.register(Contact)
