from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from pydgin_auth.models import UserProfile
from django.contrib.auth.tokens import default_token_generator
import datetime
from django.utils import timezone
from django.contrib.auth import authenticate


class PydginUserAuthenticationForm(AuthenticationForm):
    '''Overwriting the clean function to get lowercase username'''
    def clean(self):
        username = self.cleaned_data.get('username').lower()
        password = self.cleaned_data.get('password')

        if username and password:
            self.user_cache = authenticate(username=username,
                                           password=password)
            if self.user_cache is None:
                raise forms.ValidationError(
                    self.error_messages['invalid_login'],
                    code='invalid_login',
                    params={'username': self.username_field.verbose_name},
                )
            else:
                self.confirm_login_allowed(self.user_cache)

        return self.cleaned_data


class PydginUserCreationForm(UserCreationForm):
    '''£xtended user form with is_terms_agreed field'''
    is_terms_agreed = forms.BooleanField(label="Terms and conditions", required=True)
    email = forms.EmailField(label="Email address", max_length=254, required=True)
    username = forms.CharField(max_length=254, label="Username", required=True)
    is_active = False

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2", "is_terms_agreed", "is_active")

    def clean_username(self):
        '''change username to lowercase'''
        username = self.cleaned_data['username'].lower()
        try:
            User.objects.get(username=username)
            raise forms.ValidationError('A user with that username already exists')
        except User.DoesNotExist:
            return username

    def save(self, commit=True):
        if not commit:
            raise NotImplementedError("Can't create User and UserProfile without database save")

        user = super(PydginUserCreationForm, self).save(commit=True)

        token = default_token_generator.make_token(user)
        date_expires = timezone.now() + datetime.timedelta(2)

        user_profile = UserProfile(user=user,
                                   is_terms_agreed=self.cleaned_data['is_terms_agreed'],
                                   activation_key=token, key_expires=date_expires)
        user_profile.save()
        return user_profile
