''' Used to define Elastic mapping and index data. '''
from django.core.management.base import BaseCommand
from optparse import make_option
import logging
from django.contrib.contenttypes.models import ContentType
from elastic.elastic_settings import ElasticSettings
from elastic.search import Search
import json
import datetime

# Get an instance of a logger
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    ''' Elastic index model management tool.
    Note: Extend it to delete the index type from elastic server as well.
    ./manage.py manage_models --applabel=elastic
    '''
    help = "Use it to remove stale Elastic index types - models\n\n" \
           "Options:\n" \
           " --applabel [app name] " \
           " --content_type [content_type]" \

    option_list = BaseCommand.option_list + (
        make_option('--applabel',
                    dest='applabel',
                    help='applabel to do the cleanup'),
        make_option('--content_type',
                    dest='content_type',
                    help='content_type to do the cleanup'),
        )


    def handle(self, *args, **options):
        ''' Handle the user options to remove stale contenttypes - eg: applabel=elastic'''
        if options['applabel']:
            self.delete_stale_contenttypes(self, *args, **options)
        if options['content_type']:
            self.get_context_models_to_delete(self, *args, **options)
        else:
            print(help)

    def delete_stale_contenttypes(self, *args, **options):

        ContentType.objects.clear_cache()

        # find out the models to be deleted here, by setting some criteria (time limit)
        # Assuming that you have the model to be delete
        # models2go = ['cp_stats_ud-ud-tmpvsl4_inn_idx_type']

        models2go = self.get_models_to_delete()

        for model in models2go:
            for ct in ContentType.objects.filter(app_label=options['applabel']):
                if str(ct.name).endswith(model+'_idx_type'):
                    #logger.debug('Matched, finding permissions for %s  %s' % (str(ct.name), str(ct.id)))
                    #logger.debug("deleting %s" % ct)
                    ct.delete()

    

    def get_context_models_to_delete(self, *args, **options):
        '''Get models to delete'''
        ct = options['content_type']
        retDict = dict()
        retDict['acknowledged'] = 0
        logger.debug(ct)
        idx_key = 'CP_STATS_UD'
        idx = ElasticSettings.idx(idx_key)
        ''' Check if an index type exists in elastic and later check there is a contenttype/model for the given elastic index type. '''  # @IgnorePep8
        elastic_url = ElasticSettings.url()
        url = idx + '/_mapping'
        response = Search.elastic_request(elastic_url, url, is_post=False)
        if "error" in response.json():
            logger.warn(response.json())
            retDict['errorMsg'] = response.json()
            self.stdout.write(json.dumps(retDict))

        # get idx_types from _mapping
        elastic_mapping = json.loads(response.content.decode("utf-8"))
        ## fix needed if we deploy aliasing for indices 
        idx = list(elastic_mapping.keys())[0]
        idx_types = list(elastic_mapping[idx]['mappings'].keys())
        logger.debug(idx_types)

        # add idx_types that have no docs
        for idx_type in idx_types:
            if idx_type != ct:
                continue
            logger.debug("Found " + idx_type + "  equal to " + ct)
            ndocs = Search(idx=idx, idx_type=idx_type).get_count()['count']
            #logger.debug(Search(idx=idx, idx_type=idx_type).get_json_response())
            logger.debug("WE have " + str(ndocs))
            if(ndocs > 0):
                for cnt in ContentType.objects.filter():
                    if str(cnt.name).endswith(ct+'_idx_type'):
                        logger.debug('Matched, finding permissions for %s  %s' % (str(cnt.name), str(cnt.id)))
                        logger.debug("deleting %s" % ct)
                        cnt.delete()
        retDict['acknowledged'] = 1
        #logger.debug(retDict)
        self.stdout.write(json.dumps(retDict))
    
    
    def get_models_to_delete(self):

        '''Get models to delete'''
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
        ## fix needed if we deploy aliasing for indices 
        idx = list(elastic_mapping.keys())[0]
        idx_types = list(elastic_mapping[idx]['mappings'].keys())

        models2go = []
        expire_days = 7  # 1 week

        # add idx_types that have no docs
        for idx_type in idx_types:
            ndocs = Search(idx=idx, idx_type=idx_type).get_count()['count']

            if(ndocs > 0):
                models2go.append(idx_type)

            # add idx_types that were not accessed for a given time period
            url = idx + '/' + idx_type + '/_meta'
            response = Search.elastic_request(elastic_url, url, is_post=False)
            elastic_meta = json.loads(response.content.decode("utf-8"))
            if '_source' in elastic_meta:
                uploaded_str_date = elastic_meta['_source']['uploaded']
                yymmdd_str = uploaded_str_date.split()[0]
                # Format: 2015-11-03 14:43:54.099645+00:00
                from datetime import datetime as dt
                dt = dt.strptime(yymmdd_str, '%Y-%m-%d')
                uploaded_date = dt.date()

                d1 = datetime.date.today()
                d2 = d1 - datetime.timedelta(days=expire_days)
                if uploaded_date < d2:
                     models2go.append(idx_type)

        return models2go
