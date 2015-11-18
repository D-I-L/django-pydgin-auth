''' Module to handle permissions..Permissions should be granted via the admin interface'''
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import Permission, User
import logging
from django.shortcuts import get_object_or_404
from pydgin_auth.elastic_model_factory import ElasticPermissionModelFactory as elastic_factory
logger = logging.getLogger(__name__)


def get_authenticated_idx_and_idx_types(user=None, idx_keys=None, idx_type_keys=None):
    ''' Check permissions on elastic indexes and returns indexes that the given user can see'''

    # get all public idx_keys and idx_type_keys
    (idx_keys_public, idx_type_keys_public) = elastic_factory.get_idx_and_idx_type_keys(auth_public=True)

    # get all the private idx_keys and idx_type_keys
    (idx_keys_private, idx_type_keys_private) = elastic_factory.get_idx_and_idx_type_keys(auth_public=False)

    # user is None...return all public keys
    if user is None:
        return idx_keys_public, idx_type_keys_public

    idx_keys_auth = []
    idx_type_keys_auth = []

    # idx_keys or idx_type_keys is None, first fetch and add public keys
    # if idx_keys is None or idx_type_keys is None:

    if idx_keys is None:
        # First add all the public idx keys
        idx_keys_auth.extend(idx_keys_public)
        # Assign the idx keys that need to be checked
        idx_keys = idx_keys_private
    else:
        # don't add all, limit the one that the user has passed
        idx_keys_auth = [idx_key for idx_key in idx_keys if idx_key in idx_keys_public]

    if idx_type_keys is None:
        # First add all the public idx type keys
        idx_type_keys_auth.extend(idx_type_keys_public)
        # Assign the idx type keys that need to be checked
        idx_type_keys = idx_type_keys_private
    else:
        # don't add all, limit the one that the user has passed
        idx_type_keys_auth = [idx_key for idx_key in idx_type_keys if idx_key in idx_type_keys_public]

    # get elastic model names for the idx_keys and types
    (model_names_idx, model_names_idx_types) = elastic_factory.get_elastic_model_names(idx_keys=idx_keys,
                                                                                           idx_type_keys=idx_type_keys)  # @IgnorePep8
    # check if the user has permissions to see the idx model
    model_names_idx_auth = _check_content_type_perms(model_names_idx, user)
    # check if the user has permissions to see the idx type model
    model_names_idx_types_auth = _check_content_type_perms(model_names_idx_types, user)

    # finally get the actual idx keys from model names and return them
    (idx_auth, idx_types_auth) = elastic_factory.get_keys_from_model_names(model_names_idx_auth,
                                                                           model_names_idx_types_auth)

    if idx_auth is not None and len(idx_auth) > 0:
        for idx in idx_auth:
            if idx not in idx_keys_auth:
                idx_keys_auth.append(idx)

    if idx_types_auth is not None and len(idx_types_auth) > 0:
        for idx in idx_types_auth:
            if idx not in idx_type_keys_auth:
                idx_type_keys_auth.append(idx)

    return (idx_keys_auth, idx_type_keys_auth)


def _check_content_type_perms(idx_model_names, user):
    ''' Fetch content type and apply it as filter to Permission models,
     and check if the user has perm to see the code_name'''
    idx_model_names_auth = []
    for idx in idx_model_names:
        app_name = elastic_factory.PERMISSION_MODEL_APP_NAME
        model_name = idx
        content_type = None
        try:
            content_type = ContentType.objects.get(model=model_name.lower(), app_label=app_name)
        except:
            pass
            # logger.debug('Content type not found for ' + str(model_name))

        permissions = None
        if content_type:
            permissions = Permission.objects.filter(content_type=content_type)

            if permissions:
                if user is not None and user.is_authenticated():
                    for perm in permissions:
                        perm_code_name = app_name + '.' + perm.codename
                        if user.has_perm(perm_code_name):
                            idx_model_names_auth.append(idx)
            else:
                idx_model_names_auth.append(idx)

    return idx_model_names_auth


def get_user_groups(user):
    '''Get all users in a given group'''
    current_user = get_object_or_404(User, pk=user.id)
    current_user_groups = []
    user_groups = current_user.groups.all()
    for group in user_groups:
        current_user_groups.append(group.name)

    return current_user_groups
