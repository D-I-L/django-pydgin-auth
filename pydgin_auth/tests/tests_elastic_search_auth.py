''' Test for Elastic authorization & authentication'''
from django.test import TestCase
from elastic.elastic_settings import ElasticSettings
from django.conf import settings
from django.test.utils import override_settings
from pydgin_auth.tests.settings_idx import OVERRIDE_SETTINGS_PYDGIN


class ElasticSearchAuthTest(TestCase):

    def setUp(self):
        if 'pydgin_auth' in settings.INSTALLED_APPS:
            from pydgin_auth.elastic_model_factory import ElasticPermissionModelFactory
            from django.contrib.auth.models import Group
            # create elastic models
            ElasticPermissionModelFactory.create_dynamic_models()
            # create the default group READ
            Group.objects.get_or_create(name='READ')

    def tearDown(self):
        if 'pydgin_auth' in settings.INSTALLED_APPS:
            from django.contrib.auth.models import Group, User, Permission

            Group.objects.filter().delete()
            User.objects.filter().delete()
            Permission.objects.filter().delete()

    @override_settings(ELASTIC=OVERRIDE_SETTINGS_PYDGIN)
    def test_search_props(self):

        if 'pydgin_auth' in settings.INSTALLED_APPS:
            from pydgin_auth.elastic_model_factory import ElasticPermissionModelFactory
            from django.contrib.contenttypes.models import ContentType
            from django.contrib.auth.models import Group, User, Permission
            from django.shortcuts import get_object_or_404

            ElasticPermissionModelFactory.create_dynamic_models()
            search_props = ElasticSettings.search_props("ALL")

            idx = search_props['idx']
            idx_keys = search_props['idx_keys']
            idx_type = search_props['idx_type']

            self.assertIn('publications', idx, 'publications found in idx')
            self.assertIn('MARKER', idx_keys, 'MARKER found in idx_keys')
            self.assertIn('rs_merge', idx_type, 'rs_merge found in idx_type')

            # CREATE DIL group and add test_dil user to that group
            dil_group, created = Group.objects.get_or_create(name='DILX')
            self.assertTrue(created)
            dil_user = User.objects.create_user(
                username='test_dil2', email='test_dil2@test.com', password='test123')
            dil_user.groups.add(dil_group)
            self.assertTrue(dil_user.groups.filter(name='DILX').exists())

            # create permission for MARKER and IC
            test_model_name = 'marker-ic_idx_type'
            # create permissions on models and retest again to check if the idx type could be seen
            content_type, created = ContentType.objects.get_or_create(
                model=test_model_name, app_label="elastic",
            )

            # get the permission ... already created
            can_read_permission = Permission.objects.get(content_type=content_type)
            self.assertEqual('can_read_marker-ic_idx_type', can_read_permission.codename, "idx type permission correct")
            # as soon as the permission is set for an index, the index becomes a restricted resource
            idx_types_visible = ElasticSettings.search_props("ALL")["idx_type"]
            self.assertFalse('immunochip' in idx_types_visible,  'immunochip idx type not visible')

            # now grant permission to dil_user and check if idx type is visible
            dil_group.permissions.add(can_read_permission)
            dil_user = get_object_or_404(User, pk=dil_user.id)
            idx_types_visible = ElasticSettings.search_props("ALL", dil_user)["idx_type"]
            self.assertTrue('immunochip' in idx_types_visible,  'immunochip idx type visible now')
