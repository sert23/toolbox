__author__ = 'antonior'

from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^ncbiparser', views.NCBI.as_view(), name="ncbi"),
    url(r'^ensemlparser', views.Ensembl.as_view(), name="ensembl"),
    url(r'^rnacentralparser', views.RNAcentral.as_view(), name="rnacentral"),
    url(r'^fasubset', views.Fasubset.as_view(), name="fasubset"),
    url(r'^trnaparser', views.Trna.as_view(), name="trna"),
    url(r'^removedup', views.RemoveDup.as_view(), name='removedup'),
    url(r'^extract', views.Extract.as_view(), name="EXTRACT"),
    url(r'^results_fasubset', views.result_Fasubset, name="result_Fasubset"),
    url(r'results', views.result, name='helper'),
    #url(r'^run/([A-za-z]+)', views.run),
    url(r'^results', views.result),

]
