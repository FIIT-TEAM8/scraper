# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

from database import Database

# useful for handling different item types with a single interface
from itemadapter import ItemAdapter


# class GoogleNewsPipeline:
#     def process_item(self, item, spider):
#         return item


class MongoPipeline(object):
    def __init__(self):
        Database.initialize()


    def process_locale(self, locale):
        region = locale
        language = locale

        if '-' in locale:
            region = locale.split('-')[1]
            language = locale.split('-')[0]

        return region, language


    def process_item(self, item, spider):
        title = item['title'][0]
        published = item['published'][0]
        link = item['link'][0]
        html = item['html']
        region, language = self.process_locale(item['locale'])
        field_list = ['title', 'published', 'link', 'region', 'language', 'html']
        to_insert = {}

        # creates dictionary from item values
        for field in field_list:
            to_insert[field] = eval(field)
        
        # inserts into collection if document doesnt exist
        Database.insert("articles", to_insert)
        return item