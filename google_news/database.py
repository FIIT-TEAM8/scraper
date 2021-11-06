import pymongo
import google_news.settings as settings


class Database(object):
    DATABASE = None

    @staticmethod
    def initialize():
        connection = pymongo.MongoClient(
            settings.MONGODB_SERVER,
            settings.MONGODB_PORT
        )
        Database.DATABASE = connection[settings.MONGODB_DB]
        articles = Database.DATABASE[settings.MONGODB_ARTICLES]
        crime_maps = Database.DATABASE[settings.MONGODB_CRIMEMAPS]
        error_links = Database.DATABASE[settings.MONGODB_ERRORLINKS]
    
        articles.create_index('link', unique=True)
        crime_maps.create_index('link', unique=True)
        error_links.create_index('link', unique=True)


    @staticmethod
    def insert(collection, document):
        Database.DATABASE[collection].insert(document)