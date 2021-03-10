from .views import MirG

from django.conf.urls import url
from . import views

urlpatterns = [
    # url(r'results', views.result_new, name='srnabench'),
    #url(r'results', views.result),
    url(r'results', views.results, name='mirnagfree'),
    url(r'pile', views.ajax_fetch_pile, name='pile'),
    url(r'table/(.+)/(.+)/(.+)*', views.render_table, name='table_mirg'),
    url(r'^upload/[A-za-z0-9]+', views.upload_files.as_view(), name="upload"),
    url(r'^ajax_input$', views.ajax_receive_input, name='ajax_input'),
    url(r'^ajax_barplot$', views.ajax_barplot, name='ajax_barplot'),
    url(r'^ajax_pie$', views.ajax_pie, name='ajax_pie'),
    url(r'^ajax_del$', views.ajax_del, name='ajax_del'),
    url(r'^ajax_drop$', views.ajax_dropbox, name='ajax_drop'),
    url(r'^ajax_drive$', views.ajax_drive, name='ajax_drive'),
    url(r'^launch$', views.MirGLaunch.as_view(), name='launch'),
    url(r'add_sample/', views.upload_files, name='upload'),
    url(r'align/(.+)/(.+)/(.+)', views.show_align, name='show_align'),
    # url(r'run$', views.run, name='run_bench'),
    url(r'^$', MirG.as_view(),  name="MIRG"),
    # url(r'test$', views.test),
]
