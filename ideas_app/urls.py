from django.urls import path
from . import views

app_name = "ideas_app"

urlpatterns = [
    path("", views.ideas_list, name="ideas_list"),
    path("explore/<int:repo_idea_id>/", views.explore_idea, name="explore_idea"),
    path("update-feedback/<int:detail_id>/", views.update_feedback, name="update_feedback"),
    path("deep-dive/<int:detail_id>/", views.deep_dive_idea, name="deep_dive_idea"),
]