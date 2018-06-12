__author__ = 'antonior'

from django.conf.urls import url


from . import views
from miRNAfuncTargets.views import MirFuncTarget

urlpatterns = [
    url(r'^$', MirFuncTarget.as_view(), name="MIRFUNC"),
    url(r'results', views.result),
    url(r'run$', views.run),
    url(r'^/*$', views.input),
    url(r'test$', views.test),

]
