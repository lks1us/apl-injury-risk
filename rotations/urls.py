from django.urls import path

from . import views


urlpatterns = [
    path("", views.DashboardView.as_view(), name="dashboard"),
    path("clubs/", views.ClubListView.as_view(), name="club_list"),
    path("players/", views.PlayerListView.as_view(), name="player_list"),
    path("players/add/", views.player_create, name="player_create"),
    path("players/<int:pk>/", views.PlayerDetailView.as_view(), name="player_detail"),
    path("players/<int:pk>/load/add/", views.training_load_create, name="training_load_create"),
    path("players/<int:pk>/assessment/add/", views.assessment_create, name="assessment_create"),
    path("players/<int:pk>/rotation/add/", views.rotation_plan_create, name="rotation_plan_create"),
    path("rotation/", views.RotationBoardView.as_view(), name="rotation_board"),
]
