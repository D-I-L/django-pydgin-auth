"""
Django settings for pydgin_auth app

For more information on this file, see
https://docs.djangoproject.com/en/1.7/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.7/ref/settings/

LOGIN_EXEMPT_URLS is used by login_required_middleware
"""
import os
import sys


LOGIN_REDIRECT_URL = '/'

LOGIN_EXEMPT_URLS = (r'^pydgin_auth',
                     r'^accounts',
                     r'^admin',
                     r'^auth_test/$',
                     r'^$',
                     )
RUN_PERMS_MODEL = True

# BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PYDGIN_AUTH_DIR = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(PYDGIN_AUTH_DIR, 'local_apps'))
ELASTIC_PERMISSION_MODEL_APP_NAME = 'elastic'
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
