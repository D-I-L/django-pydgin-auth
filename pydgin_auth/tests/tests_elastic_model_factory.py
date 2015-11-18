''' Test for elastic model factory '''
from django.test import TestCase, override_settings

from django.contrib.auth.models import Group, User
from pydgin_auth.tests.settings_idx import OVERRIDE_SETTINGS_CHICP,\
    OVERRIDE_SETTINGS_PYDGIN
from pydgin_auth.elastic_model_factory import ElasticPermissionModelFactory as elastic_factory
from elastic.elastic_settings import ElasticSettings
from django.test.client import Client, RequestFactory
from django.utils import timezone
from os.path import os


class ElasticModelFactoryTest(TestCase):

    def setUp(self):
        '''Create test user and test client'''
        self.client = Client()
        self.factory = RequestFactory()
        self.default_group, created = Group.objects.get_or_create(name='READ')  # @UnusedVariable

        self.user = User.objects.create_user(
            username='test_user_ef', email='test_ef@test.com', password='test_pass')
        self.user.groups.add(self.default_group)

    @override_settings(ELASTIC=OVERRIDE_SETTINGS_CHICP)
    def test_get_idx_and_idx_type_keys_cp(self):
        '''create idx and idxtype keys for chicp'''
        elastic_factory.create_dynamic_models()
        # usually you can get the IDX dict via ElasticSettings.attrs().get('IDX')
        (idx_keys, idx_type_keys) = elastic_factory.get_idx_and_idx_type_keys(auth_public=False)

        # private idx
        self.assertIn('TARGET_MIFSUD', idx_keys)
        self.assertIn('CP_STATS_UD', idx_keys)

        # private idx types
        self.assertIn('CP_STATS_IC.IC-MS_IMSGC', idx_type_keys)
        self.assertIn('CP_STATS_IC.IC-JIA_HINKS_UK', idx_type_keys)
        self.assertIn('CP_STATS_IC.IC-NAR_FARACO', idx_type_keys)
        self.assertIn('CP_STATS_GWAS.GWAS-BARRETT', idx_type_keys)
        self.assertIn('CP_STATS_GWAS.GWAS-ANDERSON', idx_type_keys)
        self.assertIn('CP_STATS_GWAS.GWAS-STAHL', idx_type_keys)
        self.assertIn('CP_STATS_GWAS.GWAS-OKADA', idx_type_keys)

        # public idx
        (idx_keys, idx_type_keys) = elastic_factory.get_idx_and_idx_type_keys(auth_public=True)

        # public idx
        self.assertIn('CP_STATS_IC', idx_keys)
        self.assertIn('CP_STATS_GWAS', idx_keys)
        self.assertIn('TARGET_MARTIN', idx_keys)
        self.assertIn('TARGET_CHICAGO', idx_keys)

        # public idx and idx_type
        self.assertIn('CP_STATS_IC.IC-T1D_ONENGUT', idx_type_keys)
        self.assertIn('CP_STATS_IC.IC-ATD_COOPER', idx_type_keys)
        self.assertIn('CP_STATS_IC.IC-CEL_TRYNKA', idx_type_keys)
        self.assertIn('CP_STATS_IC.IC-RA_EYRE', idx_type_keys)
        self.assertIn('CP_STATS_IC.IC-PBC_LIU', idx_type_keys)
        self.assertIn('CP_STATS_GWAS.GWAS-COOPER', idx_type_keys)
        self.assertIn('CP_STATS_GWAS.GWAS-DUBOIS', idx_type_keys)
        self.assertIn('CP_STATS_GWAS.GWAS-FRANKE', idx_type_keys)
        self.assertIn('CP_STATS_GWAS.GWAS-IMSGC', idx_type_keys)

    @override_settings(ELASTIC=OVERRIDE_SETTINGS_PYDGIN, INCLUDE_USER_UPLOADS=False)
    def test_get_idx_and_idx_type_keys_pydgin(self):
        '''create idx and idxtype keys for chicp'''
        elastic_factory.create_dynamic_models()

        # get all private idx and keys
        (idx_keys, idx_type_keys) = elastic_factory.get_idx_and_idx_type_keys(auth_public=False)

        # private idx keys
        self.assertIn('DISEASE', idx_keys)

        # public idx keys
        self.assertNotIn('GENE', idx_keys)
        self.assertNotIn('MARKER', idx_keys)
        self.assertNotIn('PUBLICATION', idx_keys)

        # private idx type keys
        self.assertIn('DISEASE.DISEASE', idx_type_keys)
        self.assertIn('GENE.PATHWAY', idx_type_keys)
        self.assertIn('GENE.INTERACTIONS', idx_type_keys)
        self.assertIn('PUBLICATION.PUBLICATION', idx_type_keys)

        # public idx type keys
        self.assertNotIn('GENE.GENE', idx_type_keys)
        self.assertNotIn('MARKER.MARKER', idx_type_keys)

        # get all public idx and keys
        (idx_keys, idx_type_keys) = elastic_factory.get_idx_and_idx_type_keys(auth_public=True)

        # private idx key
        self.assertNotIn('DISEASE', idx_keys)

        # public idx key
        self.assertIn('MARKER', idx_keys)
        self.assertIn('PUBLICATION', idx_keys)
        self.assertIn('GENE', idx_keys)

        # private idx type keys
        self.assertNotIn('DISEASE.DISEASE', idx_type_keys)
        self.assertNotIn('GENE.PATHWAY', idx_type_keys)
        self.assertNotIn('GENE.INTERACTIONS', idx_type_keys)
        self.assertNotIn('PUBLICATION.PUBLICATION', idx_type_keys)

        # public idx type keys
        self.assertIn('GENE.GENE', idx_type_keys)
        self.assertIn('MARKER.MARKER', idx_type_keys)
        self.assertIn('MARKER.MARKER', idx_type_keys)
        self.assertIn('MARKER.MARKER', idx_type_keys)

    @override_settings(ELASTIC=OVERRIDE_SETTINGS_PYDGIN, INCLUDE_USER_UPLOADS=False)
    def test_get_elastic_model_names_pydgin(self):
        '''check whether the right model names are created for pydgin'''

        # for pydgin, returns only models for private idx and idx_types
        (model_names_idx, model_names_idx_types) = elastic_factory.get_elastic_model_names()
        model_names = model_names_idx + model_names_idx_types

        self.assertIn('disease_idx', model_names)
        self.assertIn('gene-pathway_idx_type', model_names)
        self.assertIn('marker-ic_idx_type', model_names)
        self.assertIn('disease-disease_idx_type', model_names)

    @override_settings(ELASTIC=OVERRIDE_SETTINGS_CHICP)
    def test_get_elastic_model_names_chicp(self):
        '''check whether the right model names are created for chicp'''
        elastic_factory.create_dynamic_models()
        (idx_keys, idx_type_keys) = elastic_factory.get_idx_and_idx_type_keys(auth_public=False)

        (model_names_idx, model_names_idx_types) = elastic_factory.get_elastic_model_names(
            idx_keys=idx_keys,
            idx_type_keys=idx_type_keys)

        self.assertIn('target_mifsud_idx', model_names_idx)
        self.assertIn('cp_stats_ic-ic-ms_imsgc_idx_type', model_names_idx_types)
        self.assertIn('cp_stats_ic-ic-nar_faraco_idx_type', model_names_idx_types)
        self.assertIn('cp_stats_gwas-gwas-okada_idx_type', model_names_idx_types)
        self.assertIn('cp_stats_gwas-gwas-stahl_idx_type', model_names_idx_types)

    @override_settings(ELASTIC=OVERRIDE_SETTINGS_CHICP, INCLUDE_USER_UPLOADS=True)
    def test_create_idx_type_model_permissions(self):
        elastic_settings_before = ElasticSettings.attrs().get('IDX')
        user_types_before = elastic_settings_before['CP_STATS_UD']['idx_type']
        self.assertEqual({}, user_types_before, 'CP_STATS_UD idx_type is empty')

        idx = "cp:hg19_userdata_bed"
        new_upload_file = "tmp_newly_uploaded_file"
        idx_type = new_upload_file

        os.system("curl -XPUT "+ElasticSettings.url()+"/"+idx+"/_mapping/"+idx_type+" -d '{\"" +
                  idx_type + "\":{ \"properties\" : {\"message\" : {\"type\" : \"string\", \"store\" : true } } }}'")

        os.system("curl -XPUT "+ElasticSettings.url()+"/"+idx+"/"+idx_type+"/_meta -d '{\"label\": \"" +
                  new_upload_file + "\", \"owner\": \""+self.user.username+"\", \"uploaded\": \"" +
                  str(timezone.now())+"\"}'")

        elastic_settings_after = elastic_factory.create_idx_type_model_permissions(self.user,
                                                                                   indexKey='CP_STATS_UD',
                                                                                   indexTypeKey='UD-'+new_upload_file.upper(),  # @IgnorePep8
                                                                                   new_upload_file="tmp_newly_uploaded_file")  # @IgnorePep8

        # elastic_settings_after = elastic_factory.get_elastic_settings_with_user_uploads(elastic_settings_before)
        user_types_after = elastic_settings_after['CP_STATS_UD']['idx_type']
        self.assertTrue(len(user_types_after) > 0, "Has user idx_types ")
        self.assertTrue('UD-TMP_NEWLY_UPLOADED_FILE' in user_types_after)
        self.assertEqual(user_types_after['UD-TMP_NEWLY_UPLOADED_FILE']['type'], 'tmp_newly_uploaded_file')

    @override_settings(ELASTIC=OVERRIDE_SETTINGS_PYDGIN, INCLUDE_USER_UPLOADS=False)
    def test_elastic_models_pydgin(self):
        '''check whether the right models are created for pydgin'''
        elastic_factory.create_dynamic_models()
        # check model names are created correctly

        expected_models = ['disease_idx', 'gene-pathway_idx_type', 'gene-interactions_idx_type',
                           'marker-ic_idx_type', 'publication-publication_idx_type', 'disease-disease_idx_type']

        existing_models = elastic_factory.get_db_models(existing=True)

        for model in expected_models:
            self.assertIn(model, existing_models, 'Model exists: ' + model)

    @override_settings(ELASTIC=OVERRIDE_SETTINGS_PYDGIN, INCLUDE_USER_UPLOADS=False)
    def test_get_keys_from_model_names(self):

        idx_model_names = ['disease_idx', 'gene_idx']
        idx_type_model_names = ['gene-interactions_idx_type', 'marker-ic_idx_type', 'publication-publication_idx_type']

        (idx_keys, idx_type_keys) = elastic_factory.get_keys_from_model_names(idx_model_names,
                                                                              idx_type_model_names)
        self.assertTrue('DISEASE' in idx_keys, 'got right idx key : DISEASE')
        self.assertTrue('GENE' in idx_keys, 'got right idx key : GENE')

        self.assertTrue('GENE.INTERACTIONS' in idx_type_keys, 'got right idx type key : GENE.INTERACTIONS')
        self.assertTrue('MARKER.IC' in idx_type_keys, 'got right idx type key : MARKER.IC')
        self.assertTrue('PUBLICATION.PUBLICATION' in idx_type_keys, 'got right idx type key : PUBLICATION.PUBLICATION')
