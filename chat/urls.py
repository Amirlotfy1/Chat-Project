from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path('', views.chat_index, name='index'),
    path('room/<str:room_name>/', views.room, name='room'),
    path('start_pv/<str:username>/', views.start_pv, name='start_pv'),
    path('delete_chat/<str:room_name>/', views.delete_chat, name='delete_chat'),
    path('signup/', views.signup, name='signup'),
]