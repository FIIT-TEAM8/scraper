import os
import sys
import json
from telnetlib import EL
import pymongo
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
    def index_article(article_id, document):
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

        # article's html
        article_column_value = document[Elastic.article_column]

        response = Elastic.es_connection.index(
            index=Elastic.elastic_index_name,
            doc_type='_doc',
            id=article_id, # document id in Elasticsearch == article id in articles collection
            document=json.dumps(
                {Elastic.elastic_field: article_column_value}
            )
        )

        # inform user about not indexed article
        if 'result' not in response:
            print('FAIL TO INDEX ARTICLE: {} AND RESPONSE DOESN\'T HAVE result FIELD'.format(article_id))
        elif response['result'] != 'created' and response['result'] != 'updated':
            print('FAIL TO INDEX ARTICLE: {}, RESPONSE RESULT: {}'.format(article_id, response['result']))