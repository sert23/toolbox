__author__ = 'antonior'

from django.conf.urls import url
from animalconstarget.views import AMirConsTarget

from . import views

urlpatterns = [
    url(r'results', views.result, name='mirconstarget'),

    url(r'results', views.result, name='animalconstarget'),
    url(r'^$', AMirConsTarget.as_view(), name="MIRCONS"),


    #url(r'^/*$', views.),
    #url(r'^/*$', views.input),
    #url(r'run$', views.run),
    #url(r'result', views.result),
    url(r'test$', views.test),
]

