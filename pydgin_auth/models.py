'''Creates UserProfile model, proxy GlobalPermission model and authtoken via post_save signal'''
from django.db import models
from django.contrib.auth.models import User, Group
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_save
from django.dispatch.dispatcher import receiver
from rest_framework.authtoken.models import Token


@receiver(post_save, sender=User, dispatch_uid='pydgin_auth.models.user_post_save_handler')
def user_post_save(sender, instance, created, **kwargs):
    """ This method is executed whenever an user object is created """
    if created:
        # add the user to READ group
        instance.groups.add(Group.objects.get(name='READ'))

        # create the authtoken
        Token.objects.get_or_create(user=instance)


class UserProfile(models.Model):
    """Extention for user model..added is_terms_agreed as an extra field"""
    user = models.ForeignKey(User, unique=True)
    is_terms_agreed = models.BooleanField(default=False)

    User._meta.get_field('email')._unique = True  # @UndefinedVariable
    # Create profile automatically when referenced
    User.profile = property(lambda u: UserProfile.objects.get_or_create(user=u)[0])


class GlobalPermissionManager(models.Manager):
    """ModelManager to manage GlobalPermission"""
    def get_query_set(self):
        return super(GlobalPermissionManager, self).\
            get_query_set().filter(content_type__name='global_permission')


class GlobalPermission(Permission):
    """ A global permission, not attached to a model"""

    objects = GlobalPermissionManager()

    class Meta:
        proxy = True
        verbose_name = "global_permission"

    def save(self, *args, **kwargs):
        ct, created = ContentType.objects.get_or_create(
            model=self._meta.verbose_name, app_label=self._meta.app_label,
        )
        print("Status of " + self._meta.verbose_name + " is  " + created)
        self.content_type = ct
        super(GlobalPermission, self).save(*args, **kwargs)
