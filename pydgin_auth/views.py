'''Manage views for pydgin_auth'''
from django.shortcuts import render, get_object_or_404
from django.core.context_processors import csrf
from django.contrib.auth import authenticate, login
from django.template.context import RequestContext
from pydgin_auth.forms import PydginUserCreationForm,\
    PydginUserAuthenticationForm
import os.path
from django.contrib.auth.decorators import login_required
from rest_framework.authtoken.models import Token
import logging
from django.conf import settings
from django.contrib.auth import views as auth_views
from django.contrib.auth.views import logout
from django.core.mail import send_mail
from pydgin_auth.models import UserProfile
from django.utils import timezone

logger = logging.getLogger(__name__)


def login_user(request, template_name='registration/login.html', extra_context=None):
    '''intercepts the login call and delegates to auth login '''
    if 'remember_me' in request.POST:
        request.session.set_expiry(1209600)  # 2 weeks

    response = auth_views.login(request, template_name=template_name,
                                authentication_form=PydginUserAuthenticationForm,
                                extra_context=extra_context)
    return response


def login_home(request):
    '''renders login home page'''
    return render(request, 'registration/login.html')


def permission_denied(request):
    '''renders permission denied page'''
    return render(request, 'registration/permission_denied.html')


@login_required(login_url='/accounts/login/')
def profile(request, extra_context=None):
    '''renders user profile page'''
    try:
        token = Token.objects.get_or_create(user=request.user)
    except Token.DoesNotExist:
        logging.debug('Exception while creating tokens')
        pass

    request_context = RequestContext(request)
    request_context.push({"api_key": token})

    if extra_context is not None:
        request_context.update(extra_context)

    group_list = request.user.groups.values_list('name', flat=True)
    print(group_list)

    request_context.push({"groups": group_list})

    return render(request, 'registration/profile.html', context_instance=request_context)


def registration_complete(request):
    '''renders registration complete page'''
    return render(request, 'registration/registration_form_complete.html')


def register(request, extra_context=None):
    '''register a new user after agreeing to terms and condition'''
    # read the terms and conditions file
    curr_path = os.path.dirname(os.path.realpath(__file__))
    with open(curr_path + "/templates/registration/IMB_TOC_draft.html", "r", encoding="utf-8") as myfile:
        terms_n_condition_txt = myfile.read().replace('\n', '<br/>')

    try:
        base_html_dir = settings.BASE_HTML_DIR
    except AttributeError:
        base_html_dir = ''

    token = {}

    if request.method == 'POST':
        form = PydginUserCreationForm(request.POST)
        if form.is_valid():
            new_user = form.save()
            new_user.backend = 'django.contrib.auth.backends.ModelBackend'
            new_user = authenticate(username=form.cleaned_data['username'].lower(),
                                    password=form.cleaned_data['password1'],
                                    email=form.cleaned_data['email'],
                                    is_terms_agreed=form.cleaned_data['is_terms_agreed'])

            # login(request, new_user)
            if new_user and new_user.is_authenticated:
                '''We have to login once so the last login date is set'''
                login(request, new_user)

                request_context = RequestContext(request)
                request_context.push({"basehtmldir": base_html_dir})
                request_context.push({"first_name": new_user.first_name})
                request_context.push({"last_name": new_user.last_name})
                request_context.push({"user_name": new_user.username})
                request_context.push({"user_email": new_user.email})

                logout(request)

                has_send = send_email_confirmation(request, new_user)

                request_context = RequestContext(request)
                request_context.push({"basehtmldir": base_html_dir})

                if has_send:
                    request_context.push({"success_registration": True})
                    return render(request, 'registration/registration_form_complete.html', request_context)
                else:
                    request_context.push({"failure_registration": True})
                    return render(request, 'registration/registration_form_complete.html', request_context)
            else:
                print('new_user is not authenticated')
        else:
            '''not a valid form'''
            # print(form.error_messages)
    else:
        form = PydginUserCreationForm()

    token.update(csrf(request))
    token['form'] = form
    token['terms_n_condition'] = terms_n_condition_txt
    token['basehtmldir'] = base_html_dir

    return render(request, 'registration/registration_form.html', token)


def send_email_confirmation(request, new_user):
    ''' sends email with activation key to the user '''
    email = new_user.email
    user_profile = new_user.profile
    username = new_user.username
    token = user_profile.activation_key
    host = request.get_host()

    # Send an email with the confirmation link
    email_subject = 'Your new  account confirmation'
    email_body = "Hello, %s, and thanks for signing up for an %s account!\n\nTo activate your account,\
                click the link given below within 48 hours:\n\nhttp://%s/accounts/user/activate/%s" % (username,
                                                                                                       host, host,
                                                                                                       token)
    has_send = send_mail(email_subject, email_body, 'immunobase-feedback@cimr.cam.ac.uk', [email])
    return has_send


def activate(request, activation_key):
    '''view to activate the user by enabling is_activate,
    provided the right activation_key is given and the link was activated before the expiry period '''

    try:
        base_html_dir = settings.BASE_HTML_DIR
    except AttributeError:
        base_html_dir = ''

    request_context = RequestContext(request)
    request_context.push({"basehtmldir": base_html_dir})
    request_context.push({"login_url": '/accounts/login/'})

    if request.user.is_authenticated():
        '''if user is authenticated, it means he is already a registered user'''
        request_context.push({"has_account": True})
        return render(request, 'registration/registration_form_complete.html', request_context)

    user_profile = get_object_or_404(UserProfile,
                                     activation_key=activation_key)

    if user_profile.key_expires < timezone.now():
        '''key has expired'''
        request_context.push({"expired": True})
        return render(request, 'registration/registration_form_complete.html', request_context)

    user_account = user_profile.user
    user_account.is_active = True
    user_account.save()

    request_context.push({"success_activation": True})
    request_context.push({"user": user_account})
    return render(request, 'registration/registration_form_complete.html', request_context)
