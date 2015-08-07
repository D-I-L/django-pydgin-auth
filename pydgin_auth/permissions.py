''' Module to handle permissions..Permissions should be granted via the admin interface'''
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import Permission, User
import logging
from django.shortcuts import get_object_or_404
logger = logging.getLogger(__name__)
from pydgin_auth.admin import ElasticPermissionModelFactory


def check_index_perms(user, idx_names):
    ''' Check permissions on elastic indexes and returns indexes that the given user can see'''
    logger.debug('Before permission check ' + str(idx_names))
    idx_names_auth = []
    for idx in idx_names:
        app_name = ElasticPermissionModelFactory.PERMISSION_MODEL_APP_NAME
        model_name = idx.lower() + ElasticPermissionModelFactory.PERMISSION_MODEL_SUFFIX

        content_type = ContentType.objects.get(model=model_name, app_label=app_name)
        logger.debug('Checking permissions for ' + str(content_type))
        permissions = Permission.objects.filter(content_type=content_type)

        if permissions:
            if user.is_authenticated():
                for perm in permissions:
                    perm_code_name = app_name + '.' + perm.codename
                    if user.has_perm(perm_code_name):
                        idx_names_auth.append(idx)
        else:
            idx_names_auth.append(idx)

    logger.debug('After permission check' + str(idx_names_auth))
    return idx_names_auth


def check_has_permission(user, idx):
    app_name = ElasticPermissionModelFactory.PERMISSION_MODEL_APP_NAME
    model_name = idx.lower() + ElasticPermissionModelFactory.PERMISSION_MODEL_SUFFIX

    content_type = ContentType.objects.get(model=model_name, app_label=app_name)
    logger.debug('Checking permissions for ' + str(content_type))
    permissions = Permission.objects.filter(content_type=content_type)

    if permissions:
        if user.is_authenticated():
            for perm in permissions:
                perm_code_name = app_name + '.' + perm.codename
                if user.has_perm(perm_code_name):
                    return True
    else:
        return True

    return False


def get_user_groups(user):
    current_user = get_object_or_404(User, pk=user.id)
    current_user_groups = []
    user_groups = current_user.groups.all()
    for group in user_groups:
        current_user_groups.append(group.name)

    return current_user_groups
