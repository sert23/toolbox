from django.conf.urls import include, url
# from dajaxice.core import dajaxice_autodiscover, dajaxice_config
# dajaxice_autodiscover()

import views

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns =[
    #url(r'^/*', views.index),
    url(r'^jobstatus/', include('progress.urls')),
    url(r'^srnafuncterms', include('sRNAfuncTerms.urls')),
    url(r'^srnade', include('sRNAde.urls')),
    url(r'^srnablast', include('sRNAblast.urls')),
    url(r'^srnabench', include('sRNABench.urls')),
    url(r'^srnajbrowserde', include('sRNAdejBrowser.urls')),
    url(r'^srnajbrowser', include('sRNAjBrowser.urls')),
    url(r'^srnagfree', include('sRNAgFree.urls')),
    url(r'^mirconstarget', include('miRNAconstarget.urls')),
    url(r'^mirnafunctargets', include('miRNAfuncTargets.urls')),
    url(r'^helper/', include('helpers.urls')),
    url(r'^blank$', views.blank),
    url(r'^index', views.index),
    url(r'^manual', views.manual),
    url(r'^search', views.search),
    url(r'^barleyCultivar', views.cultivar),
    url(r'^versionControl', views.version, name='versions'),
    url(r'^/*$', views.index, name='home'),
    # url(dajaxice_config.dajaxice_url, include('dajaxice.urls')),
]

