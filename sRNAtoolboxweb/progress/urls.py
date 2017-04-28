__author__ = 'antonior'

from django.conf.urls import url
import views

urlpatterns = [
    url(r'^/([A-za-z]+)', views.progress),
]
