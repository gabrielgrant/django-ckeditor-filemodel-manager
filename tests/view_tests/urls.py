from django.conf.urls.defaults import *

from django.contrib import admin
import ckeditor_filemodel_manager as manager

admin.autodiscover()
manager.autodiscover()

urlpatterns = patterns('',
    # can this be made to work somehow? should it?
    #(r'^filemodel_manager/',
    #	include('ckeditor_filemodel_manager.urls')
    #),
    
    (r'^manager/', include(manager.site.urls)),
    (r'^admin/', include(admin.site.urls)),
    #(r'^accounts/', include('login.urls')),
    
    # Static media
    (r'^static/(?P<path>.*)', 'django.views.static.serve',
        {'document_root':
           './static/'}),
    
    # Static media
    (r'^media/(?P<path>.*)', 'django.views.static.serve',
        {'document_root':
           '/tmp/ckeditor_filemodel_manager_test_media/'}),
)

#print urlpatterns[0]
#print urlpatterns[0].urlpatterns
