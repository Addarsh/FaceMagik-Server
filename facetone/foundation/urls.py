from django.urls import path

from . import views

urlpatterns = [
    path('user/', views.TestUser.as_view(), name='user'),
    path('session/', views.Session.as_view(), name='session'),
]