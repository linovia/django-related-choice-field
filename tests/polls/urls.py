try:
	from django.conf.urls import patterns, include, url
except ImportError:
	from django.conf.urls.defaults import patterns, include, url

from .views import MyFormView, MySecondFormView

urlpatterns = patterns('',
    url(r'^$', MyFormView.as_view()),
    url(r'^2/$', MySecondFormView.as_view()),
)
