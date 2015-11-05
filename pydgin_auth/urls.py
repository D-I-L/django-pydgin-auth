'''URLs for pydgin_auth and  django auth'''
from django.conf.urls import url
from django.contrib import admin
import django.contrib.auth.views
import pydgin_auth.views
from django.conf import settings
from pydgin_auth.views import activate

admin.autodiscover()

try:
    base_html_dir = settings.BASE_HTML_DIR
except AttributeError:
    base_html_dir = ''


# Registration URLs
urlpatterns = [url(r'^login/$',  pydgin_auth.views.login_user, {"extra_context": {"basehtmldir": base_html_dir}}),
               url(r'^logout/$', django.contrib.auth.views.logout, {'next_page': '/'}),
               url(r'^profile/$',  pydgin_auth.views.profile, {"extra_context": {"basehtmldir": base_html_dir}}),
               url(r'^permission_denied/$',  pydgin_auth.views.permission_denied),
               url(r'^register/$', pydgin_auth.views.register),
               url(r'^register/complete/$', pydgin_auth.views.registration_complete),
               url(r'^user/activate/(?P<activation_key>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
                   activate, name='user_activation_link'),
               url(r'^user/password/reset/$', django.contrib.auth.views.password_reset,
                   {'post_reset_redirect': '/accounts/user/password/reset/done/',
                    'template_name': 'registration/admin/password_reset_form.html',
                    'email_template_name': 'registration/admin/password_reset_email.html',
                    'subject_template_name': 'registration/admin/password_reset_subject.txt',
                    'extra_context': {"basehtmldir": base_html_dir},
                    },
                   name="password_reset",
                   ),
               url(r'^user/password/reset/done/$', django.contrib.auth.views.password_reset_done,
                   {'template_name': 'registration/admin/password_reset_done.html',
                    'extra_context': {"basehtmldir": base_html_dir}}),
               url(r'^user/password/reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
                   django.contrib.auth.views.password_reset_confirm,
                   {'post_reset_redirect': '/accounts/user/password/done/',
                    'template_name': 'registration/admin/password_reset_confirm.html',
                    'extra_context': {"basehtmldir": base_html_dir},
                    },
                   name="password_reset_confirm"),
               url(r'^user/password/done/$', django.contrib.auth.views.password_reset_complete,
                   {'template_name': 'registration/admin/password_reset_complete.html',
                    'extra_context': {"basehtmldir": base_html_dir}},
                   ),
               ]
