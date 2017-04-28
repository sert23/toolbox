__author__ = 'antonior'

from django.conf.urls import url


import views

urlpatterns = [
    url(r'^/*$', views.de),
    url(r'run$', views.run),
    url(r'result', views.result),
    url(r'test$', views.test),
]
