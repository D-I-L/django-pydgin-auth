from django.test import TestCase
from django.core.management import call_command
from elastic.tests.settings_idx import IDX
from elastic.elastic_settings import ElasticSettings

from elastic.search import Search, ElasticQuery
from elastic.query import Query, TermsFilter, BoolQuery
import requests
from django.contrib.auth.models import User, Group, Permission
from pydgin_auth.permissions import get_user_groups,\
    get_authenticated_idx_and_idx_types
from django.test.client import Client, RequestFactory
# Get an instance of a logger
import logging
import json
from django.test.utils import override_settings
from pydgin_auth.elastic_model_factory import ElasticPermissionModelFactory as elastic_factory
from pydgin_auth.tests.settings_idx import OVERRIDE_SETTINGS_PYDGIN,\
    OVERRIDE_SETTINGS_CHICP
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404
logger = logging.getLogger(__name__)


class PydginAuthElasticTestCase(TestCase):

    multi_db = True

    def setUp(self):
        ''' Run the index loading script to create test indices and
        create test user '''

        region_key = 'PRIVATE_REGIONS_GFF'
        if region_key in IDX.keys():
            idx_kwargs = IDX[region_key]
            self.index_name = idx_kwargs['indexName']
            call_command('index_search', **idx_kwargs)

        '''Create test user and test client'''
        self.client = Client()
        self.factory = RequestFactory()
        self.default_group, created = Group.objects.get_or_create(name='READ')  # @UnusedVariable

        self.user = User.objects.create_user(
            username='test_user', email='test@test.com', password='test_pass')
        self.user.groups.add(self.default_group)

    def tearDown(self):
        ''' Remove loaded test indices and test repository. '''

        key = 'PRIVATE_REGIONS_GFF'
        if key in IDX.keys():
            print(ElasticSettings.url() + '/' + IDX[key]['indexName'])
            requests.delete(ElasticSettings.url() + '/' + IDX[key]['indexName'])

    def test_region_idx_loader(self):
        ''' Test loader has created and populated indices.  '''

        key = 'PRIVATE_REGIONS_GFF'

        if key in IDX.keys():
            idx = IDX[key]['indexName']
            Search.index_refresh(idx)
            self.assertTrue(Search.index_exists(idx=idx), 'Index exists: '+idx)
            ndocs = Search(idx=idx).get_count()['count']
            self.assertTrue(ndocs > 0, "Elastic count documents in " + idx + ": " + str(ndocs))

    @override_settings(ELASTIC=OVERRIDE_SETTINGS_PYDGIN)
    def test_get_authenticated_idx_and_idx_types(self):

        elastic_factory.create_dynamic_models()

        # As user is none we should get back only public idx and idx_type keys
        (idx_keys_auth, idx_type_keys_auth) = get_authenticated_idx_and_idx_types(user=None)

        self.assertIn('MARKER', idx_keys_auth)
        self.assertIn('GENE', idx_keys_auth)
        self.assertIn('PUBLICATION', idx_keys_auth)

        self.assertIn('MARKER.MARKER', idx_type_keys_auth)
        self.assertIn('MARKER.HISTORY', idx_type_keys_auth)
        self.assertIn('GENE.GENE', idx_type_keys_auth)

        # As user is not none and we have assigned the user to any group we should get back
        # only public idx and idx_type keys
        (idx_keys_auth, idx_type_keys_auth) = get_authenticated_idx_and_idx_types(self.user)

        self.assertIn('MARKER', idx_keys_auth)
        self.assertIn('GENE', idx_keys_auth)
        self.assertIn('PUBLICATION', idx_keys_auth)

        self.assertIn('MARKER.MARKER', idx_type_keys_auth)
        self.assertIn('MARKER.HISTORY', idx_type_keys_auth)
        self.assertIn('GENE.GENE', idx_type_keys_auth)

        # Create test_dil user and assign the user to DIL group
        dil_group, created = Group.objects.get_or_create(name='DIL')
        self.assertTrue(created)
        dil_user = User.objects.create_user(
            username='test_dil', email='test_dil@test.com', password='test123')
        dil_user.groups.add(dil_group)
        self.assertTrue(dil_user.groups.filter(name='DIL').exists())

        all_groups_of_dil_user = dil_user.groups.values_list('name', flat=True)
        self.assertTrue("DIL" in all_groups_of_dil_user, "Found DIL in groups")
        self.assertTrue("READ" in all_groups_of_dil_user, "Found READ in groups")

        # get private idx and assign permission to dil_user
        (model_names_idx, model_names_idx_types) = elastic_factory.get_elastic_model_names(auth_public=False)

        test_idx_model = model_names_idx[0]
        test_idx_type_model = model_names_idx_types[1]

        self.assertTrue(test_idx_model.endswith('_idx'), 'Idx model ends with _idx')
        self.assertTrue(test_idx_type_model.endswith('_idx_type'), 'Idx type model ends with _idx_type')

        # create permissions on models and retest again to check if the idx could be seen
        content_type_idx, created_idx = ContentType.objects.get_or_create(  # @UnusedVariable
            model=test_idx_model, app_label=elastic_factory.PERMISSION_MODEL_APP_NAME,
        )

        content_type_idx_type, created_idx_type = ContentType.objects.get_or_create(  # @UnusedVariable
            model=test_idx_type_model, app_label=elastic_factory.PERMISSION_MODEL_APP_NAME,
        )

        # The idx and idx_type should already exists in db, so created should be false
        self.assertFalse(created_idx, test_idx_model + ' is available ')
        self.assertFalse(created_idx_type, test_idx_type_model + ' is available ')

        self.assertIsNotNone(content_type_idx, content_type_idx.name + ' is not None')
        self.assertIsNotNone(content_type_idx_type, content_type_idx_type.name + ' is not None')

        # create permission and assign ...Generally we create via admin interface
        can_read_permission_idx, create_permission_idx = Permission.objects.get_or_create(  # @UnusedVariable
            content_type=content_type_idx)
        self.assertIsNotNone(can_read_permission_idx, ' Permission is available ' + can_read_permission_idx.name)

        can_read_permission_idx_type, create_permission_idx = Permission.objects.get_or_create(  # @UnusedVariable
            content_type=content_type_idx_type)
        self.assertIsNotNone(can_read_permission_idx_type,
                             ' Permission is available ' + can_read_permission_idx_type.name)

        # now grant access to test_dil and check if the user can see the index
        # Add the permission to dil_group
        dil_group.permissions.add(can_read_permission_idx)
        dil_group.permissions.add(can_read_permission_idx_type)

        dil_user = get_object_or_404(User, pk=dil_user.id)
        available_group_perms = dil_user.get_group_permissions()

        self.assertTrue('elastic.can_read_' + test_idx_model.lower() in available_group_perms)
        self.assertTrue('elastic.can_read_' + test_idx_type_model.lower() in available_group_perms)

        # Try to get the authenticated idx and idx_types keys again
        (idx_keys_auth, idx_type_keys_auth) = get_authenticated_idx_and_idx_types(dil_user)

        (idx_model_name_auth, idx_type_model_name_auth) = elastic_factory.get_elastic_model_names(
            idx_keys=idx_keys_auth,
            idx_type_keys=idx_type_keys_auth)

        self.assertTrue(test_idx_model in idx_model_name_auth)
        self.assertTrue(test_idx_type_model in idx_type_model_name_auth)

        self.assertIn('MARKER', idx_keys_auth)
        self.assertIn('GENE', idx_keys_auth)
        self.assertIn('PUBLICATION', idx_keys_auth)

        self.assertIn('MARKER.MARKER', idx_type_keys_auth)
        self.assertIn('MARKER.HISTORY', idx_type_keys_auth)
        self.assertIn('GENE.GENE', idx_type_keys_auth)

        # pass just one index key and index type and check for returned keys and types
        # publication idx is public and publication.publication is private
        idx_keys = ['PUBLICATION']
        idx_type_keys = ['PUBLICATION.PUBLICATION']
        idx_keys_auth = []
        idx_type_keys_auth = []
        (idx_keys_auth, idx_type_keys_auth) = get_authenticated_idx_and_idx_types(self.user,
                                                                                  idx_keys=idx_keys,
                                                                                  idx_type_keys=idx_type_keys)
        self.assertIn('PUBLICATION', idx_keys_auth)
        self.assertNotIn('PUBLICATION.PUBLICATION', idx_type_keys_auth)

        self.assertTrue(len(idx_keys_auth) == 1, 'Got back only one idx')

    @override_settings(ELASTIC=OVERRIDE_SETTINGS_CHICP)
    def test_elastic_model_names_round_trip(self):

        # getting the private ones
        (model_names_idx, model_names_idx_types) = elastic_factory.get_elastic_model_names(auth_public=False)
        self.assertIn('target_mifsud_idx', model_names_idx, 'target_mifsud_idx found')
        self.assertIn('cp_stats_gwas-gwas-anderson_idx_type', model_names_idx_types,
                      'cp_stats_gwas-gwas-anderson_idx_type found')

        (idx_keys, idx_type_keys) = elastic_factory.get_keys_from_model_names(model_names_idx, model_names_idx_types)
        self.assertIn('TARGET_MIFSUD', idx_keys, 'TARGET_MIFSUD found')
        self.assertIn('CP_STATS_IC.IC-NAR_FARACO', idx_type_keys, 'CP_STATS_IC.IC-NAR_FARACO found')

    def test_elastic_group_name(self):
        '''
        Testing the workflow defined in: https://killin.cimr.cam.ac.uk/nextgensite/2015/08/05/region-authorization/
        Testing various elastic queries

        idx doc:
         "_source":{"attr": {"region_id": "803", "group_name": "[\"DIL\"]", "Name": "4q27"},
         "seqid": "chr4", "source": "immunobase", "type": "region",
         "score": ".", "strand": ".", "phase": ".", "start": 122061159, "end": 122684373}
        idx_query:
        Private(in given group) OR Public
        -d '{"query":{"filtered":{"filter":{"bool": {
                                            "should": [
                                                        {"terms": {"group_name":["dil"]}},
                                                        { "missing": { "field": "group_name"   }}
                                                      ]
                                                    }}}}}'
        Private(in given group):
        -d '{"query":{"filtered":{"filter":{"terms":{"group_name":["dil"]}}}}}'
        Public:
        -d {'query': {'filtered': {'filter': {'missing': {'field': 'group_name'}},
-                         'query': {'term': {'match_all': '{}'}}}}}
        '''
        # get the groups for the given user
        response = self.client.post('/accounts/login/', {'username': 'test_user', 'password': 'test_pass'})
        self.assertTrue(response.status_code, "200")

        logged_in_user = User.objects.get(id=self.client.session['_auth_user_id'])
        if logged_in_user and logged_in_user.is_authenticated():
            user_groups = get_user_groups(logged_in_user)
            self.assertTrue('READ' in user_groups, "user present in READ group")
            # make sure the user is not yet in DIL group
            self.assertFalse('DIL' in user_groups, "user not present in DIL group")

        group_names = get_user_groups(logged_in_user)
        if 'READ' in group_names : group_names.remove('READ')  # @IgnorePep8
        group_names = [x.lower() for x in group_names]
        self.assertTrue(len(group_names) == 0, "No group present")

        # Match all query, as there is no group we do a match all
        query = ElasticQuery(Query.match_all())
        expected_query_string = {"query": {"match_all": {}}}
        self.assertJSONEqual(json.dumps(query.query), json.dumps(expected_query_string), "Query string matched")

        Search.index_refresh(self.index_name)
        elastic = Search(query, idx=self.index_name)
        docs = elastic.search().docs
        self.assertTrue(len(docs) == 12, "Elastic string query retrieved all public regions")

        # Filtered query for group names, add the user to DIL group and get the query string
        self.dil_group = Group.objects.create(name='DIL')
        logged_in_user.groups.add(self.dil_group)
        group_names = get_user_groups(logged_in_user)
        if 'READ' in group_names : group_names.remove('READ')  # @IgnorePep8
        group_names = [x.lower() for x in group_names]
        self.assertTrue(len(group_names) > 0, "More than 1 group present")
        self.assertTrue("dil" in group_names, "DIL group present")

        # retrieves all docs with missing field group_name - 11 docs
        terms_filter = TermsFilter.get_missing_terms_filter("field", "group_name")
        query = ElasticQuery.filtered(Query.match_all(), terms_filter)
        elastic = Search(query, idx=self.index_name)
        docs = elastic.search().docs
        self.assertTrue(len(docs) == 11, "Elastic string query retrieved all public regions")

        # build filtered boolean query to bring all public docs + private docs 11+1 = 12 docs
        query_bool = BoolQuery()
        query_bool.should(Query.missing_terms("field", "group_name")) \
                  .should(Query.terms("group_name", group_names).query_wrap())

        query = ElasticQuery.filtered_bool(Query.match_all(), query_bool)
        elastic = Search(query, idx=self.index_name)
        docs = elastic.search().docs
        self.assertTrue(len(docs) == 12, "Elastic string query retrieved both public + private regions")

        terms_filter = TermsFilter.get_terms_filter("group_name", group_names)
        query = ElasticQuery.filtered(Query.match_all(), terms_filter)
        elastic = Search(query, idx=self.index_name)
        docs = elastic.search().docs
        self.assertTrue(len(docs) == 1, "Elastic string query retrieved one private regions")
        self.assertEqual(docs[0].attr['Name'], "4q27", "type matched region")
        self.assertEqual(docs[0].attr['region_id'], "803", "type matched region")
        self.assertEqual(docs[0].attr['group_name'], "[\"DIL\"]", "type matched region")
