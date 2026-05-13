from django.urls import path
from . import views

app_name = 'cacheapp'

urlpatterns = [
    path('', views.index, name='index'),
    path('generate/', views.generate_page, name='generate_page'),
    path('upload/', views.upload_payload, name='upload_payload'),
    path('copy/', views.copy_file, name='copy_file'),
    path('cache/viewer/', views.cache_viewer, name='cache_viewer'),
    path('profile/', views.profile, name='profile'),
    path('cache/trigger/', views.cache_trigger, name='cache_trigger'),
]