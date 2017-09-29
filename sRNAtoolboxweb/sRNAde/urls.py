__author__ = 'antonior'

from django.conf.urls import url
from . import views

urlpatterns = [
    #url(r'^ncbiparser', views.NCBI.as_view(), name="ncbi"),
    url(r'^/*$', views.De.as_view(), name="DE"),
    url(r'^/*$', views.de),
    # url(r'run$', views.run, name='run_de'),
    url(r'result', views.result, name='results_de'),
    url(r'test$', views.test),

]
