from django.urls import path
from django.shortcuts import render
from . import views
urlpatterns = [
    path('', views.blog, name='blog'),
    path('<slug:slug>', views.post, name='post'),
    path('prev/<slug:slug>', views.post_preview, name='post_preview'),
]