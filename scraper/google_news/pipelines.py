# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

from database import Database
from elastic import Elastic

# useful for handling different item types with a single interface
from itemadapter import ItemAdapter

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
        keywords = item['keywords']

        field_list = ['title', 'published', 'link', 'region', 'language', 'html']
        to_insert = {}

        # creates dictionary from item values
        for field in field_list:
            to_insert[field] = eval(field)
        
        # inserts into collection if document doesnt exist
        article_id = Database.insert("articles", to_insert)

        item['article_id'] = article_id

        return item

class ElasticsearchPipeline:
    def __init__(self):
        Elastic.initialize()

    def process_item(self, item, spider):
        article_id = item['article_id']
        
        Elastic.index_article(article_id, item)

        return item