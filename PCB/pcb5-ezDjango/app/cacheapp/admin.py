from django.contrib import admin
from .models import CacheItem


@admin.register(CacheItem)
class CacheItemAdmin(admin.ModelAdmin):
    list_display = ('key', 'created_at')
    search_fields = ('key',)
    readonly_fields = ('created_at',)