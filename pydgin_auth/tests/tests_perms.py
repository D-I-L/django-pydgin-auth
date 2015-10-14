from django.test import TestCase
from django.contrib.auth.models import User, Group
from django.test.client import RequestFactory, Client
import logging

logger = logging.getLogger(__name__)


class PydginAuthTestCase(TestCase):

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

    def test_register_user(self):
        '''Test registration. First try to login with out agreeing to terms and
        try to register again with is_terms_agreed set'''
        logger.debug('running test_register_user')
        response = self.client.get('/accounts/register/', follow=True)
        # check if redirected to registration page
        self.assertTemplateUsed(response, 'registration/registration_form.html')
        response = self.client.post('/accounts/register/',
                                    {'username': 'new_user', 'email': 'newuser@new.com',
                                     'password1': 'newtest', 'password2': 'newtest'})
        self.assertEqual(response.status_code, 200)

        users = User.objects.all()
        user_present = False
        for user in users:
            if user.username == 'new_user':
                user_present = True
                break

        self.assertFalse(user_present, "new_user not in Users before is_terms_agreed")

        response = self.client.post('/accounts/register/',
                                    {'username': 'new_user', 'email': 'newuser@new.com',
                                     'password1': 'newtest', 'password2': 'newtest', 'is_terms_agreed': '1'})

        users = User.objects.all()
        for user in users:
            if user.username == 'new_user':
                user_present = True
                break

        self.assertTrue(user_present, "new_user in Users list after is_terms_agreed")

        # try to create user with same user name
        response = self.client.post('/accounts/register/',
                                    {'username': 'new_user', 'email': 'newuser@new.com',
                                     'password1': 'newtest', 'password2': 'newtest', 'is_terms_agreed': '1'})
        self.assertEqual(response.status_code, 200)

        self.assertContains(response, 'User with this Email address already exists')
        self.assertContains(response, 'A user with that username already exists')

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
