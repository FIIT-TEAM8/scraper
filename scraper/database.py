import os
import sys
import json
import pymongo
import google_news.settings as settings
from elasticsearch import Elasticsearch


class Database(object):
    DATABASE = None
    # connect to elasticsearch
    es_connection = None

    elastic_index_name = settings.ELASTIC_INDEX_NAME
    elastic_index_config = settings.ELASTIC_INDEX_CONFIG
    elastic_field = settings.ELASTIC_FIELD
    article_column_value = settings.MONGO_COLUMN

    @staticmethod
    def initialize():
        connection = pymongo.MongoClient(settings.MONGODB_URI)
        Database.DATABASE = connection[settings.MONGODB_DB]
        articles = Database.DATABASE[settings.MONGODB_ARTICLES]
        crime_maps = Database.DATABASE[settings.MONGODB_CRIMEMAPS]
        error_links = Database.DATABASE[settings.MONGODB_ERRORLINKS]

        Database.es_connection = Elasticsearch(hosts=[
            {
                "host": settings.ES_HOST,
                "port": int(settings.ES_PORT)
            }
        ])

        articles.create_index('link', unique=True)
        crime_maps.create_index('link', unique=True)
        error_links.create_index('link', unique=True)


    @staticmethod
    def insert(collection, document):
        article_id = Database.DATABASE[collection].insert(document)

        # make sure connection is set
        if Database.es_connection is None:
            print('Article with id {} wasn\'t indexed, because connection to Elasticsearch wasn\'t established.'.format(article_id))
            return

        if not Database.es_connection.indices.exists(index=Database.elastic_index_name):
            # firstly load index configuration
            with open(os.getcwd() + '/' + Database.elastic_index_config) as articles_config_file:
                configuration = json.load(articles_config_file)

                # create index
                res = Database.es_connection.indices.create(index=Database.elastic_index_name, settings=configuration["settings"])
                
                # make sure index was created
                if not res['acknowledged']:
                    print('Index wasn\'t created')
                    print(res)
                    sys.exit()
                else:
                    print('Index successfully created.')

        Database.es_connection.index(
            index=Database.elastic_index_name,
            doc_type='_doc',
            id=article_id, # document id in Elasticsearch == article id in articles collection
            document=json.dumps(
                {Database.elastic_field: Database.article_column_value}
            )
        )

    @staticmethod
    def update(collection, link, to_update):
        Database.DATABASE[collection].update_one({'link': link}, 
                                                 {'$addToSet': {'keywords': to_update}}, upsert=True)