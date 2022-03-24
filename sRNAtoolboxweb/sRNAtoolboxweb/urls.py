from django.conf.urls import include, url
from django.contrib import admin

from sRNAtoolboxweb import views

urlpatterns =[
    #url(r'^/*', views.index),
    url(r'^jobstatus/', include('progress.urls')),
    url(r'^srnafuncterms', include('sRNAfuncTerms.urls')),
    url(r'^srnade/', include('sRNAde.urls')),
    url(r'^srnablast/', include('sRNAblast.urls')),
    url(r'^srnabench/', include('sRNABench.urls')),
    url(r'^srnajbrowserde', include('sRNAdejBrowser.urls')),
    url(r'^srnajbrowser', include('sRNAjBrowser.urls')),
    url(r'^srnagfree', include('sRNAgFree.urls')),
    url(r'^mirgfree/', include('miRNAgFree.urls')),
    url(r'^mirconstarget', include('miRNAconstarget.urls')),
    url(r'^amirconstarget/', include('animalconstarget.urls')),
    url(r'^pmirconstarget/', include('plantconstarget.urls')),
    url(r'^mirnafunctargets', include('miRNAfuncTargets.urls')),
    url(r'^multibench', include('multibench.urls')),
    url(r'^newbench/', include('newbench.urls')),
    url(r'^helper/', include('helpers.urls')),
    url(r'^srnacons/', include('sRNAcons.urls')),
    url(r'^blank$', views.blank),
    url(r'^index', views.index),
    url(r'^manual', views.manual),
    url(r'^search', views.search),
    url(r'^testing', views.testing),
    url(r'^barleyCultivar', views.cultivar),
    url(r'^statistics', views.version, name='versions'),
    url(r'^database', views.database_content, name='databases'),
    url(r'^manage', views.management, name='manage'),
    url(r'^/*$', views.index, name='home'),
    url(r'^admin/', admin.site.urls),
    url(r'^multiupload/', include('multi.urls', namespace='multi')),
]

