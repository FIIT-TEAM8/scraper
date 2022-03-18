import os
import sys
import json
from telnetlib import EL

from attr import field
import google_news.settings as settings
from elasticsearch import Elasticsearch


class Elastic(object):
    es_connection = None

    elastic_index_name = settings.ELASTIC_INDEX_NAME
    elastic_index_config = settings.ELASTIC_INDEX_CONFIG
    elastic_field = settings.ELASTIC_FIELD
    article_column = settings.MONGO_COLUMN

    @staticmethod
    def initialize():
        Elastic.es_connection = Elasticsearch(hosts=[
            {
                "host": settings.ES_HOST,
                "port": int(settings.ES_PORT)
            }
        ])


    @staticmethod
    def index_article(article_id, item):
        # make sure connection is set
        if Elastic.es_connection is None:
            print('Article with id {} wasn\'t indexed, because connection to Elasticsearch wasn\'t established.'.format(article_id))
            return

        if not Elastic.es_connection.indices.exists(index=Elastic.elastic_index_name):
            # firstly load index configuration
            with open(os.getcwd() + '/' + Elastic.elastic_index_config) as articles_config_file:
                configuration = json.load(articles_config_file)

                # create index
                res = Elastic.es_connection.indices.create(index=Elastic.elastic_index_name, settings=configuration["settings"])
                
                # make sure index was created
                if not res['acknowledged']:
                    print('Index wasn\'t created')
                    print(res)
                    sys.exit()
                else:
                    print('Index successfully created.')

        # create dictionary from GoogleNewsItem, because GoogleNewsItem is not JSON serializable
        # ommit article_id, because it is not in elastic index as a field
        article_data = {field_name: field_value for field_name, field_value in item.items() if field_name != 'article_id'}

        response = Elastic.es_connection.index(
            index=Elastic.elastic_index_name,
            doc_type='_doc',
            id=article_id, # document id in Elasticsearch == article id in articles collection
            document=json.dumps(article_data)
        )

        # inform user about not indexed article
        if 'result' not in response:
            print('FAIL TO INDEX ARTICLE: {} AND RESPONSE DOESN\'T HAVE result FIELD'.format(article_id))
        elif response['result'] != 'created' and response['result'] != 'updated':
            print('FAIL TO INDEX ARTICLE: {}, RESPONSE RESULT: {}'.format(article_id, response['result']))