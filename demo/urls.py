from django.conf.urls.defaults import patterns, include, url

from polls.views import MyFormView, MySecondFormView

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', MyFormView.as_view()),
    url(r'^2/$', MySecondFormView.as_view()),
    url(r'^admin/', include(admin.site.urls)),
)
