from .views import MirG

from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'results', views.result_new, name='srnabench'),
    #url(r'results', views.result),
    url(r'table/(.+)/(.+)/(.+)*', views.render_table, name='table_bench'),
    url(r'^upload/[A-za-z0-9]+', views.upload_files.as_view(), name="upload"),
    url(r'^ajax_input$', views.ajax_receive_input, name='ajax_input'),
    url(r'^ajax_del$', views.ajax_del, name='ajax_del'),
    url(r'add_sample/', views.upload_files, name='upload'),
    url(r'align/(.+)/(.+)/(.+)', views.show_align, name='show_align'),
    # url(r'run$', views.run, name='run_bench'),
    url(r'^$', MirG.as_view(),  name="MIRG"),
    url(r'test$', views.test),
]
