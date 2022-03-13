import os
import sys
import json
import pymongo
import google_news.settings as settings

class Database(object):
    DATABASE = None

    @staticmethod
    def initialize():
        connection = pymongo.MongoClient(settings.MONGODB_URI)
        Database.DATABASE = connection[settings.MONGODB_DB]
        articles = Database.DATABASE[settings.MONGODB_ARTICLES]
        crime_maps = Database.DATABASE[settings.MONGODB_CRIMEMAPS]
        error_links = Database.DATABASE[settings.MONGODB_ERRORLINKS]

        articles.create_index('link', unique=True)
        crime_maps.create_index('link', unique=True)
        error_links.create_index('link', unique=True)


    @staticmethod
    def insert(collection, document):
        article_id = Database.DATABASE[collection].insert(document)

        return article_id

    @staticmethod
    def update(collection, link, to_update):
        Database.DATABASE[collection].update_one({'link': link}, 
                                                 {'$addToSet': {'keywords': to_update}}, upsert=True)