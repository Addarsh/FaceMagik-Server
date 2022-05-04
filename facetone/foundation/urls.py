from django.urls import path

from . import views, user_session

urlpatterns = [
    path('user/', views.TestUser.as_view(), name='user'),
    path('session/', views.Session.as_view(), name='session'),
    path('user_session/rotation_image/', user_session.RotationImage.as_view(), name='rotation_image'),
    path('user_session/rotation_result/', user_session.RotationResult.as_view(), name='rotation_result'),
    path('user_session/', user_session.UserSession.as_view(), name='user_session'),
]