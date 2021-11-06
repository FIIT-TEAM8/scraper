from scrapy.crawler import CrawlerProcess
from google_news.spiders.spider import Spider
from scrapy.utils.project import get_project_settings
import json
from database import Database

process = CrawlerProcess(get_project_settings())

process.crawl(Spider)
process.start()

# connect to mongo database
Database.initialize()


try:
    # fields in crimemaps and errorlinks collections
    field_list = ["link", "keywords"]

    # save article urls and crime keywords to database
    print("Saving links & crime keywords ...")
    for key in Spider.article_links:
        link = key
        keywords = Spider.article_links[key]
        to_insert = {}

        for field in field_list:
            to_insert[field] = eval(field)

        Database.insert("crimemaps", to_insert)

    # save respones with status code other than 200 to databse
    print("Saving error links ...")
    for key in Spider.error_links:
        link = key
        keywords = Spider.error_links[key]
        to_insert = {}

        for field in field_list:
            to_insert[field] = eval(field)
            
        Database.insert("errorlinks", to_insert)

except Exception:
    pass