__author__ = 'antonior'

from django.conf.urls import url
from sRNAblast.views import SRNABlast


from . import views

urlpatterns = [
    url(r'results', views.result, name='srnablast'),
    url(r'^/*$', SRNABlast.as_view(),name="SRNABLAST"),
    #url(r'^/*$', views.input),
    url(r'run$', views.run),
    url(r'result', views.result),
    url(r'test$', views.test),
]
