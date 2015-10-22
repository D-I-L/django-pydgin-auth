from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from pydgin_auth.models import UserProfile
from django.contrib.auth.tokens import default_token_generator
import datetime
from django.utils import timezone


class PydginUserCreationForm(UserCreationForm):
    '''£xtended user form with is_terms_agreed field'''
    is_terms_agreed = forms.BooleanField(label="Terms and conditions", required=True)
    email = forms.EmailField(label="Email address", max_length=254, required=True)
    is_active = False

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2", "is_terms_agreed", "is_active")

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
