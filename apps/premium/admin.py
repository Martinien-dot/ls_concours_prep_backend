from django.contrib import admin
from .models import PremiumCode


@admin.register(PremiumCode)
class PremiumCodeAdmin(admin.ModelAdmin):
    list_display = ('id', 'is_used', 'used_by', 'created_at', 'used_at')
    list_filter = ('is_used', 'created_at')
    search_fields = ('used_by__email',)
    readonly_fields = ('code_hash', 'used_by', 'used_at', 'created_at')