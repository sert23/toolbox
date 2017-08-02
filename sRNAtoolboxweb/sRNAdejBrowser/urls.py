__author__ = 'antonior'

from django.conf.urls import url


from . import views

urlpatterns = [
    url(r'^/*$', views.input),
    url(r'run$', views.run),
    url(r'result', views.result),
    url(r'test', views.test),
]
