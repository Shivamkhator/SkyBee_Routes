from django.urls import path
from . import views

urlpatterns = [
    path('', views.find_route_view, name='home'),
]
