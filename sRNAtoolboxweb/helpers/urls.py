__author__ = 'antonior'

from django.conf.urls import url
import views

urlpatterns = [
    url(r'^ncbiparser', views.ncbi),
    url(r'^ensemlparser', views.ens),
    url(r'^rnacentralparser', views.rnac),
    url(r'^trnaparser', views.trna),
    url(r'^removedup', views.RemoveDup.as_view(), name='removedup'),
    url(r'^extract', views.extract),
    url(r'^run/([A-za-z]+)', views.run),
    url(r'^results', views.result),
]
