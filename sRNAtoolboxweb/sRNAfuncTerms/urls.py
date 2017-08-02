__author__ = 'antonior'

from django.conf.urls import url


from . import views

urlpatterns = [
    url(r'results', views.result),
    url(r'run$', views.run),
    url(r'^/*$', views.functerms),
    url(r'test$', views.test),
]
