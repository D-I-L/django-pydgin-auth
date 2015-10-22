from django.core import mail
from django.test import TestCase
from django.conf import settings


class EmailTest(TestCase):

    '''
    Settings that should work:
    DEFAULT_FROM_EMAIL = 'immunobase-feedback@cimr.cam.ac.uk'
    SERVER_EMAIL = 'immunobase-feedback@cimr.cam.ac.uk'
    EMAIL_HOST = 'ppsw.cam.ac.uk'
    EMAIL_HOST_USER = ''  # or 'user@gmail.com'
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_PORT = 25
    EMAIL_USE_TLS = True
    '''
    def test_send_email(self):
        # Test the settings
        self.assertEqual(settings.DEFAULT_FROM_EMAIL, 'immunobase-feedback@cimr.cam.ac.uk', 'Default email is right')
        self.assertEqual(settings.SERVER_EMAIL, 'immunobase-feedback@cimr.cam.ac.uk', 'Default server email is right')
        self.assertEqual(settings.EMAIL_HOST, 'ppsw.cam.ac.uk', 'Default email host is right')

        self.assertEqual(settings.EMAIL_BACKEND, 'django.core.mail.backends.locmem.EmailBackend',
                                                 'Default email backend is right')
        self.assertEqual(settings.EMAIL_PORT, 25, 'Default email port is right')
        self.assertEqual(settings.EMAIL_USE_TLS, True, 'Default email use TLS is right')

        # Send message.
        mail.send_mail('Subject here', 'Here is the message',
                       settings.DEFAULT_FROM_EMAIL, ['to@example.com'],
                       fail_silently=False)

        # Test that one message has been sent.
        self.assertEqual(len(mail.outbox), 1)  # @UndefinedVariable

        # Verify that the subject and message is correct.
        self.assertEqual(mail.outbox[0].subject, 'Subject here')
        message = str(mail.outbox[0].message())
        self.assertTrue('Here is the message' in message, 'Found text in message')
