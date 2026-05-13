from django.db import models
from django.contrib.auth.models import User


class CacheItem(models.Model):
    key = models.CharField(max_length=255, unique=True)
    value = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.key