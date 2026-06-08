from django.contrib import admin
from core.models import Rifa

class RifaAdmin(admin.ModelAdmin):
    ...


admin.site.register(Rifa, RifaAdmin)
