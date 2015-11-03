''' Test for pydgin_auth view'''
from django.test import TestCase
from django.test.client import Client, RequestFactory
from django.contrib.auth.models import Group, User
import logging
from django.core import mail
import re
import datetime
from django.utils import timezone
from django.core.urlresolvers import resolve
from pydgin_auth.views import register

logger = logging.getLogger(__name__)


class UserRegistration(TestCase):

    multi_db = True

    def setUp(self):
        '''Method called to prepare the test , is called immediately before calling the test method.
        Create test_user and add it to READ group'''
        # Every test needs a client.
        self.client = Client()
        # Every test needs access to the request factory.
        self.factory = RequestFactory()
        self.group, created = Group.objects.get_or_create(name='READ')  # @UnusedVariable
        self.user = User.objects.create_user(
            username='test_user', email='test@test.com', password='test_pass')
        self.user.groups.add(self.group)

    def test_register_user(self):
        '''Test registration. First try to login with out agreeing to terms and
        try to register again with is_terms_agreed set'''
        logger.debug('running test_register_user')

        found = resolve('/accounts/register/')
        self.assertEqual(found.func, register)

        response = self.client.get('/accounts/register/', follow=True)
        self.assertEqual(response.status_code, 200)
        # check if redirected to registration page
        self.assertTemplateUsed(response, 'registration/registration_form.html')

        # try to register with is_terms_agreed is 0
        response = self.client.post('/accounts/register/',
                                    {'username': 'new_user', 'email': 'newuser@example.com',
                                     'password1': 'newtest', 'password2': 'newtest', 'is_terms_agreed': False})
        self.assertEqual(response.status_code, 200)

        users = User.objects.all()
        user_present = False
        for user in users:
            if user.username == 'new_user':
                user_present = True
                break

        self.assertFalse(user_present, "new_user not in Users before is_terms_agreed")

        response = self.client.post('/accounts/register/',
                                    {'username': 'new_user', 'email': 'newuser@example.com',
                                     'password1': 'newtest', 'password2': 'newtest', 'is_terms_agreed': True})

        users = User.objects.all()
        for user in users:
            if user.username == 'new_user':
                user_present = True
                current_user = user
                break

        self.assertTrue(user_present, "new_user in Users list after is_terms_agreed")
        self.assertEqual(len(mail.outbox), 1)  # @UndefinedVariable

        # Verify that the subject of the first message is correct.
        self.assertEqual(mail.outbox[0].subject, 'Your new  account confirmation')

        self.assertEqual('immunobase-feedback@cimr.cam.ac.uk',
                         mail.outbox[0].from_email, 'Got the right from email same  ' + mail.outbox[0].from_email)

        # URL format: http://testserver/accounts/user/activate/465-bf72e814043a20964bff

        p = re.compile('http[s]?://(.*?)\/accounts\/user\/activate\/([0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})')
        message = str(mail.outbox[0].message())

        url = re.search("(?P<url>https?://[^\s]+)", message).group("url")
        m = p.match(url)
        host = m.group(1)
        activation_key = m.group(2)
        self.assertEqual('testserver', host, 'host name is right')
        self.assertRegex(activation_key, '[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20}', 'activation key is of right format ')

        # now check the status of the user...is_active should be false
        self.assertEqual(current_user.username, 'new_user', 'User name is right')
        self.assertFalse(current_user.is_active, 'user is not active')
        self.assertEqual(current_user.profile.activation_key, activation_key, 'activation_key is right')
        date_expires = timezone.now() + datetime.timedelta(2)
        self.assertGreaterEqual(date_expires, current_user.profile.key_expires, 'date expires is right')

        # now try the activation link and check if the status of is_active is changed
        response = self.client.get('/accounts/user/activate/'+activation_key, follow=True)
        self.assertContains(response, 'Your account has been activated now')
        self.assertEqual(response.status_code, 200)
        activated_user = User.objects.get_by_natural_key('new_user')
        self.assertTrue(activated_user.is_active, 'user is activated successfully')

        # try to create user with same user name
        response = self.client.post('/accounts/register/',
                                    {'username': 'new_user', 'email': 'newuser@example.com',
                                     'password1': 'newtest', 'password2': 'newtest', 'is_terms_agreed': '1'})
        self.assertEqual(response.status_code, 200)

        self.assertContains(response, 'User with this Email address already exists')
        self.assertContains(response, 'A user with that username already exists')

        # try to create user with same user name in UPPER CASE
        response = self.client.post('/accounts/register/',
                                    {'username': 'NEW_USER', 'email': 'newuser@example.com',
                                     'password1': 'newtest', 'password2': 'newtest', 'is_terms_agreed': '1'})
        self.assertEqual(response.status_code, 200)

        self.assertContains(response, 'A user with that username already exists')

        # try to login with user name in UPPER CASE
        response = self.client.post('/accounts/login/', {'username': 'NEW_USER', 'password': 'newtest'})
        self.assertTrue(response.status_code, "200")
        self.assertIn('_auth_user_id', self.client.session)
        self.assertEqual(User.objects.get(id=self.client.session['_auth_user_id']).username, 'new_user')

    def test_login(self):
        '''Test login. First try to login with invalid credentials, and try again with right credentials again'''
        logger.debug('running test_login')
        response = self.client.get('/accounts/login/', follow=True)
        # check if redirected to login
        self.assertTemplateUsed(response, 'registration/login.html')

        response = self.client.post('/accounts/login/', {'username': 'test_invalid', 'password': 'test_pass'})
        self.assertTrue(response.status_code, "200")
        response_string = response.content.decode('utf-8')
        self.assertTrue("The username and password provided is not valid/recognised" in response_string)

        response = self.client.post('/accounts/login/', {'username': 'test_user', 'password': 'test_pass'})
        self.assertTrue(response.status_code, "200")
        self.assertIn('_auth_user_id', self.client.session)
        self.assertEqual(User.objects.get(id=self.client.session['_auth_user_id']).username, 'test_user')

    def test_create_groups(self):
        '''Test if we get back the READ group without creating it (created is false)
        and other groups should get created (created is True)'''
        read_group, created = Group.objects.get_or_create(name='READ')
        self.assertEqual(read_group.name, "READ")
        self.assertEqual(created, False)

        dil_group, created = Group.objects.get_or_create(name='DIL')
        self.assertEqual(dil_group.name, "DIL")
        self.assertTrue(created)

        curator_group, created = Group.objects.get_or_create(name='CURATOR')
        self.assertEqual(curator_group.name, "CURATOR")
        self.assertTrue(created)

        pydgin_admin_group, created = Group.objects.get_or_create(name='ADMIN')
        self.assertEqual(pydgin_admin_group.name, "ADMIN")
        self.assertTrue(created)
