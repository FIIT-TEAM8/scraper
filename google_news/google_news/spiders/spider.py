import time
import scrapy
from scrapy.crawler import CrawlerProcess
from gnewsparser import GnewsParser

# run with command: scrapy crawl spider -o <outputfile.csv> -t csv

class Spider(scrapy.Spider):
    name = "spider"

    # TODO: write article links with keywords to json, when last request ends
    # NOTE: find out how can program detects, that last request ends
    article_links = {} # storing article links, with crime keywords

    crime_keywords = ['murder']

    custom_settings = {
        'FEED_FORMAT': 'json',
        'FEED_URI': 'output.json'
    }

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

    def parse(self, response, link, published, title, crime_keyword):
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

                # writes data in json, but also in cmd
                # TODO: have to remove writing to cmd
                yield {
                    "title": title,
                    "published": published,
                    "link": link,
                    "html": body_tag
                }
            except:
                # if page doesn't contains body tag, program will execute this line of code
                pass

# run Spider
process = CrawlerProcess()
process.crawl(Spider)
process.start()