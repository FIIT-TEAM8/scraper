import os
import time
import scrapy
from google_news.items import GoogleNewsItem
from google_news.spiders.gnewsparser import GnewsParser

# run with command: scrapy crawl spider -o <outputfile.json>
# working directory: C:\Users\jakub\team_project\scraper\google_news\google_news

# TODO: 1. citat zlociny jeden po druhom zo suboru moricovho
# TODO: 2. zapis vsetkych zlocinov s keywords a linkami na disk

class Spider(scrapy.Spider):
    name = "spider"

    article_links = {} # storing article links, with crime keywords

    crime_keywords = ['murder']

    def start_requests(self):
        gnews_parser = GnewsParser()

        # set up searching for each crime defined in crime_keywords
        for crime_keyword in self.crime_keywords:
            gnews_parser.setup_search('murder', '2020-12-01', '2020-12-31')

            while True:
                res = gnews_parser.get_results() # getting articles on daily basis

                if res is None:
                    break

                for article in res:
                    # retrieve needed data from Google RSS
                    link = article['link']
                    title = article['title']
                    published = article['published']

                    # make get request on article link
                    yield scrapy.Request(link,
                        callback=self.parse,
                        cb_kwargs=dict(
                            link=link,
                            published=published, 
                            title=title,
                            crime_keyword=crime_keyword
                        )
                    )

                    break

                break

    def parse(self, response, link, published, title, crime_keyword):
        item = GoogleNewsItem() # this item will be writin in output file, when it is yield

        # parse only responses with status code 200
        if response.status == 200:
            try:
                # retrieve body tag with data
                body_tag = response.css('body').get()

                # initialize keywords list for article link
                if link not in self.article_links:
                    self.article_links[link] = []

                # add article keyword to list of keywords
                self.article_links[link].append(crime_keyword)

                # writes data into item, which will be yield into output file
                item['title'] = title,
                item['published'] = published,
                item['link'] = link,
                item['html'] = body_tag

                yield item

            except Exception:
                # if page doesn't contains body tag, program will execute this line of code
                pass