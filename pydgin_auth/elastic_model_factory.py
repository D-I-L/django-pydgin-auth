'''
Module to create elastic models dynamically
'''
from django.contrib import admin
from django.contrib.auth.models import Permission

from django.db import models
from django.contrib.contenttypes.models import ContentType
from elastic.elastic_settings import ElasticSettings

from django.apps import apps
from django.contrib.admin.sites import AlreadyRegistered

import logging
from django.db import connections
from django.conf import settings
from elastic.search import Search
import json

logger = logging.getLogger(__name__)


def create_elastic_index_model_manager(model_name, application_label, content_type_id):
    '''
    function to create proxy Model Managers for a given Model
    A Manager is the interface through which database query operations are provided to Django models
    '''
    className = model_name.title() + 'Manager'

    class Meta:
        proxy = True
        verbose_name = className
        app_label = application_label

    model_manager = type(className, (models.Manager, ), {'__module__': 'elastic.models',
                                                         'Meta': Meta, 'cid': content_type_id})

    def get_queryset(self):
        return super(model_manager, self).get_queryset().filter(content_type_id=self.cid)

    setattr(model_manager, 'cid', content_type_id)
    setattr(model_manager, 'get_queryset', get_queryset)
    return model_manager


def create_elastic_index_model(model_name, application_label):
    '''
    function to create proxy Models dynamically.
    Create ContentType and pass the id to the function that creates model manager
    '''

    class Meta:
        proxy = True
        verbose_name = model_name.lower()
        app_label = application_label

    ct, created = ContentType.objects.get_or_create(model=Meta.verbose_name,  # @UnusedVariable
                                                    app_label=Meta.app_label)

    # create permission
    can_read_permission, create = Permission.objects.get_or_create(  # @UnusedVariable
        codename='can_read_' + Meta.verbose_name.lower(),
        name='Can Read ' + Meta.verbose_name.lower(),
        content_type=ct)

    model_manager = create_elastic_index_model_manager(model_name, application_label, ct.id)

    attrs = {'__module__': 'elastic.models', 'Meta': Meta, 'objects': model_manager()}
    elasticmodel = type(model_name, (Permission,), attrs)
    setattr(elasticmodel, 'cid', ct.id)
    setattr(elasticmodel, 'objects', model_manager())
    return elasticmodel, created

#
# class ElasticModelAdmin(admin.ModelAdmin):
#
#     def elastic_delete_stale_ct(self, request):
#         return delete_stale_ct(request, self)
#
#     def get_urls(self):
#         return [
#             url(r'^delete_stale_ct/$', self.admin_site.admin_view(self.elastic_delete_stale_ct),
#                 name='delete_stale_ct_url'),
#         ] + super(ElasticModelAdmin, self).get_urls()


class ElasticPermissionModelFactory():
    '''class to create dynamic proxy models and managers for elastic indexes'''
    PERMISSION_MODEL_SUFFIX = '_idx'
    PERMISSION_MODEL_TYPE_SUFFIX = '_idx_type'
    PERMISSION_MODEL_NAME_TYPE_DELIMITER = '-'
    PERMISSION_MODEL_APP_NAME = settings.ELASTIC_PERMISSION_MODEL_APP_NAME

    @classmethod
    def create_dynamic_models(cls, elastic_dict=None, idx_keys=None, idx_type_keys=None):
        '''main function that delegates the call to create the proxy models and managers for elastic indexes'''
        (model_names_idx, model_names_idx_types) = cls.get_elastic_model_names(elastic_dict, idx_keys, idx_type_keys)

        model_names = model_names_idx + model_names_idx_types

        connection = connections[settings.AUTH_DB]
        if "django_content_type" in connection.introspection.table_names():
            for model_name in model_names:
                elasticmodel, created = create_elastic_index_model(model_name,  # @UnusedVariable
                                                                   cls.PERMISSION_MODEL_APP_NAME)

            cls.autoregister()

    @classmethod
    def autoregister(cls, app_label=PERMISSION_MODEL_APP_NAME):
        '''auto register all the models belonging to the given app eg: elastic'''
        for model_ct in ContentType.objects.filter(app_label=app_label):

            model = None
            try:
                model = apps.get_model(app_label=app_label, model_name=model_ct.model.lower())
            except LookupError:
                '''
                If you are here, then content type exists, and model doesn't exists
                Means, you have changed an idx from private to public
                '''
                # logger.warn('Model not found for ' + model_ct.model.lower())
                # model_name = model_ct.model.lower()
                # model, created = create_elastic_index_model(model_name,  # @UnusedVariable
                #                                            cls.PERMISSION_MODEL_APP_NAME)
            except:
                pass

            try:
                if model is not None:
                    # dmin.site.register(model, ElasticModelAdmin)
                    admin.site.register(model)
            except AlreadyRegistered:
                pass

    @classmethod
    def get_idx_and_idx_type_keys(cls, elastic_dict=None, auth_public=False):
        '''
        Returns the idx and idx type keys
        Use the auth_public flag to restrict to either public or private idx and idx_types
        '''
        if elastic_dict is None:
            elastic_dict = ElasticSettings.attrs().get('IDX')
            if settings.INCLUDE_USER_UPLOADS is True:
                elastic_dict = cls.get_elastic_settings_with_user_uploads(elastic_dict)

        idx_type_keys_public = []
        idx_type_keys_private = []

        # get private idx_keys if auth_public is False and public idx_keys otherwise
        idx_keys_public = [idx_key for (idx_key, idx_values) in elastic_dict.items()
                           if('auth_public' in idx_values and idx_values['auth_public'] is True)]
        idx_keys_private = [idx_key for (idx_key, idx_values) in elastic_dict.items()
                            if('auth_public' not in idx_values or idx_values['auth_public'] is False)]

        # get idx_type_keys
        for idx_key in idx_keys_public + idx_keys_private:
            if 'idx_type' in elastic_dict[idx_key]:
                for (idx_type_key, idx_type_values) in elastic_dict[idx_key]['idx_type'].items():

                    if 'auth_public' in idx_type_values and idx_type_values['auth_public'] is True:
                        idx_type_keys_public.append(idx_key + '.' + idx_type_key)

                    if 'auth_public' not in idx_type_values or idx_type_values['auth_public'] is False:
                        idx_type_keys_private.append(idx_key + '.' + idx_type_key)

        if auth_public:
            # make case insensitive
            idx_keys_public_icase = [x.upper() for x in idx_keys_public]
            idx_type_keys_public_icase = [x.upper() for x in idx_type_keys_public]
            return idx_keys_public_icase, idx_type_keys_public_icase
        else:
            # make case insensitive
            idx_keys_private_icase = [x.upper() for x in idx_keys_private]
            idx_type_keys_private_icase = [x.upper() for x in idx_type_keys_private]
            return idx_keys_private_icase, idx_type_keys_private_icase

    @classmethod
    def get_elastic_model_names(cls, elastic_dict=None, idx_keys=None, idx_type_keys=None, auth_public=False):
        '''Returns the model names to be created for dynamic models
        Right suffix is added to different the model types'''

        # generate models only for private idx and idx_types
        if idx_keys is None and idx_type_keys is None:
            (idx_keys, idx_type_keys) = cls.get_idx_and_idx_type_keys(elastic_dict=elastic_dict, auth_public=False)

        model_names_idx = [idx_key + ElasticPermissionModelFactory.PERMISSION_MODEL_SUFFIX for idx_key in idx_keys]

        model_names_idx_types = []
        for idx_type_key in idx_type_keys:
            idx_type_key = idx_type_key.replace('.', cls.PERMISSION_MODEL_NAME_TYPE_DELIMITER)
            model_name = idx_type_key + cls.PERMISSION_MODEL_TYPE_SUFFIX
            model_names_idx_types.append(model_name)

        # make case insensitive
        model_names_idx_icase = [model_name.lower() for model_name in model_names_idx]
        model_names_idx_types_icase = [model_name_type.lower() for model_name_type in model_names_idx_types]
        return model_names_idx_icase, model_names_idx_types_icase

    @classmethod
    def get_keys_from_model_names(cls, idx_model_names=None, idx_type_model_names=None):
        '''Returns the idx keys and idx type keys given idx and idx type model names'''

        idx_keys = [model_name.replace(ElasticPermissionModelFactory.PERMISSION_MODEL_SUFFIX,
                                       '') for model_name in idx_model_names]

        # get all idx keys
        (idx_keys_private, idx_type_keys_private) = cls.get_idx_and_idx_type_keys(auth_public=False)  # @UnusedVariable
        (idx_keys_public, idx_type_keys_public) = cls.get_idx_and_idx_type_keys(auth_public=True)  # @UnusedVariable

        idx_keys_all = idx_keys_private + idx_keys_public

        idx_type_keys = []
        for model_name in idx_type_model_names:
            for idx_key in idx_keys_all:
                if model_name.lower().startswith(idx_key.lower()):
                    model_name_no_suffix = model_name.replace(cls.PERMISSION_MODEL_TYPE_SUFFIX, '')
                    (head, idx_str, idx_type_str) = model_name_no_suffix.partition(idx_key.lower())  # @UnusedVariable
                    idx_type_str = idx_type_str.replace(cls.PERMISSION_MODEL_NAME_TYPE_DELIMITER, ".", 1)
                    idx_type_key = idx_str + idx_type_str
                    idx_type_keys.append(idx_type_key)

        idx_keys_icase = [x.upper() for x in idx_keys]
        idx_type_keys_icase = [x.upper() for x in idx_type_keys]
        return(idx_keys_icase, idx_type_keys_icase)

    @classmethod
    def get_db_models(cls, app_label=PERMISSION_MODEL_APP_NAME, existing=False):
        '''Gets the models from settings file and compares with existing elastic models from db.
           Returns only the model that does not exist in db'''
        (model_names_idx, model_names_idx_types) = cls.get_elastic_model_names()
        settings_model_names = model_names_idx + model_names_idx_types

        all_existing_models = ContentType.objects.filter(app_label=app_label)
        all_existing_model_names = [model.name for model in all_existing_models]

        all_non_existing_models = [model for model in settings_model_names if model not in all_existing_model_names]

        if existing:
            return all_existing_model_names
        else:
            return all_non_existing_models

    @classmethod
    def get_elastic_settings_with_user_uploads(cls, elastic_dict=None, new_upload_file=None):
        '''Get the updated elastic settings with user uploaded idx_types'''

        idx_key = 'CP_STATS_UD'
        idx = ElasticSettings.idx(idx_key)

        ''' Check if an index type exists in elastic and later check there is a contenttype/model for the given elastic index type. '''  # @IgnorePep8
        elastic_url = ElasticSettings.url()
        url = idx + '/_mapping'
        response = Search.elastic_request(elastic_url, url, is_post=False)

        if "error" in response.json():
            logger.warn(response.json())
            return None

        # get idx_types from _mapping
        elastic_mapping = json.loads(response.content.decode("utf-8"))
        idx_types = list(elastic_mapping[idx]['mappings'].keys())

        if elastic_dict is None:
            elastic_dict = ElasticSettings.attrs().get('IDX')

        idx_type_dict = {}

        existing_ct = [ct.name for ct in ContentType.objects.filter(app_label=cls.PERMISSION_MODEL_APP_NAME)]

        for idx_type in idx_types:

            idx_type_with_suffix = idx_type + cls.PERMISSION_MODEL_TYPE_SUFFIX

            for ct in existing_ct:
                if ct.endswith(idx_type_with_suffix):

                    meta_url = idx + '/' + idx_type + '/_meta/_source'
                    meta_response = Search.elastic_request(elastic_url, meta_url, is_post=False)

                    try:
                        elastic_meta = json.loads(meta_response.content.decode("utf-8"))
                        label = elastic_meta['label']
                    except:
                        label = "UD-" + idx_type

                    idx_type_dict['UD-' + idx_type.upper()] = {'label': label, 'type': idx_type}

        if new_upload_file is not None:
            idx_type = new_upload_file
            label = "UD-" + idx_type
            idx_type_dict['UD-' + idx_type.upper()] = {'label': label, 'type': idx_type}

        elastic_dict['CP_STATS_UD']['idx_type'] = idx_type_dict
        return elastic_dict

    @classmethod
    def create_idx_type_model_permissions(cls, user, elastic_dict=None, indexKey=None, indexTypeKey=None, new_upload_file=None):  # @IgnorePep8
        '''Create the models for the uploaded index types , create new permission and assign the permission to user
        First we have to get the updated elastic settings with user uploaded index types.  We do that by quering the
        elastic for         CP_STATS_UD index, but care should be taken that some of the models might have been deleted,
        so we add to the settings only the models that have the content types.

        '''
        try:
            if settings.INCLUDE_USER_UPLOADS is True and elastic_dict is None:
                if new_upload_file is not None:
                    elastic_dict = cls.get_elastic_settings_with_user_uploads(elastic_dict=elastic_dict, new_upload_file=new_upload_file)  # @IgnorePep8
                else:
                    new_upload_file = indexTypeKey.split("UD-", 1)[1].lower()
                    elastic_dict = cls.get_elastic_settings_with_user_uploads(elastic_dict=elastic_dict, new_upload_file=new_upload_file)  # @IgnorePep8
        except:
            pass

        if indexKey is None:
            indexKey = 'CP_STATS_UD'
        user_upload_dict = list(elastic_dict[indexKey]['idx_type'].keys())

        model_names_idx_types = []
        if indexTypeKey in user_upload_dict:

            if indexTypeKey.startswith('UD-'):
                indexTypeKey = indexKey + '.' + indexTypeKey
            else:
                indexTypeKey = indexKey + '.' + 'UD-' + indexTypeKey.upper()

            (model_names_idx, model_names_idx_types) = cls.get_elastic_model_names(elastic_dict=elastic_dict,  # @UnusedVariable @IgnorePep8
                                                                                   idx_keys=[indexKey],
                                                                                   idx_type_keys=[indexTypeKey])

            cls.create_dynamic_models(idx_keys=[indexKey], idx_type_keys=[indexTypeKey])

        existing_models = cls.get_db_models(existing=True)
        if len(model_names_idx_types) == 1 and model_names_idx_types[0] in existing_models:

            model_name = model_names_idx_types[0]
            content_type = None
            try:
                content_type = ContentType.objects.get(model=model_name.lower(),
                                                       app_label=settings.ELASTIC_PERMISSION_MODEL_APP_NAME)
            except:
                pass

            permissions = None
            perm_code_name = 'can_read_' + model_name.lower()

            if content_type:
                permissions = Permission.objects.filter(content_type=content_type)

                if permissions:
                    for perm in permissions:
                        if perm_code_name == perm.codename:
                            # assign permission to user
                            user.user_permissions.add(perm)

        return elastic_dict
