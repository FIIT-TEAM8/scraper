# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

import pymongo
import google_news.settings as settings

# useful for handling different item types with a single interface
from itemadapter import ItemAdapter


# class GoogleNewsPipeline:
#     def process_item(self, item, spider):
#         return item


class MongoPipeline(object):
    def __init__(self):
        connection = pymongo.MongoClient(
            settings.MONGODB_SERVER,
            settings.MONGODB_PORT
        )

        db = connection[settings.MONGODB_DB]
        self.articles = db[settings.MONGODB_ARTICLES]
        self.crime_maps = db[settings.MONGODB_CRIMEMAPS]
        self.error_links = db[settings.MONGODB_ERRORLINKS]


    def process_item(self, item, spider):
        self.articles.insert(dict(item))
        return item