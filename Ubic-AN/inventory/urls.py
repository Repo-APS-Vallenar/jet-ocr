from django.urls import path
from . import views

urlpatterns = [
    path('', views.map_view, name='map_view'),
    path('api/save-position/', views.save_asset_position, name='save_position'),
    path('api/unassign-asset/', views.unassign_asset, name='unassign_asset'),
]
