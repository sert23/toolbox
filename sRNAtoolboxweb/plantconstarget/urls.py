__author__ = 'antonior'

from django.conf.urls import url
from plantconstarget.views import PMirConsTarget

from . import views

urlpatterns = [
    url(r'results', views.result, name='mirconstarget'),
    url(r'results', views.result, name='animalconstarget'),
    url(r'^$', PMirConsTarget.as_view(), name="MIRCONS"),


    #url(r'^/*$', views.),
    #url(r'^/*$', views.input),
    #url(r'run$', views.run),
    #url(r'result', views.result),
    url(r'test$', views.test),
]
