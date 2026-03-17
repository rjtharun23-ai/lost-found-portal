from django.urls import path
from . import views

urlpatterns = [
    path("", views.login_view, name="login"),  # default login page

    path("home/", views.home, name="home"),
    path("lost/", views.lost_items, name="lost_items"),
    path("found/", views.found_items, name="found_items"),
    path("add/", views.add_item, name="add_item"),
    path("claim/<int:item_id>/", views.claim_item, name="claim_item"),
    path("my-claims/", views.my_claims, name="my_claims"),
    path("logout/", views.logout_view, name="logout"),
]