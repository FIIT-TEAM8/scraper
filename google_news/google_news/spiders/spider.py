from os.path import dirname

import scrapy
# probably a bad import practice? if something breaks uncomment this and comment the other import of GnewsParser :)
# from google_news.spiders.gnewsparser import GnewsParser
from ..spiders.gnewsparser import GnewsParser

# same stuff as import above
# from google_news.items import GoogleNewsItem
from ..items import GoogleNewsItem

CRIME_KEYWORD_FILE = '\\crimes\\4_part.txt'


# run with command: scrapy crawl spider -o <outputfile.json>
# working directory: C:\Users\jakub\team_project\scraper\google_news\google_news


# open crime keywords file and load them into list
def load_crime_keywords():
    crime_keywords = []
    crime_keywords_filepath = dirname(dirname(dirname(dirname(__file__))))

    with open(crime_keywords_filepath + CRIME_KEYWORD_FILE) as file:
        for line in file:
            crime_keywords.append(line.rstrip())

    return crime_keywords


class Spider(scrapy.Spider):
    name = "spider"

    article_links = {}  # storing article links, with crime keywords

    crime_keywords = load_crime_keywords()

    def start_requests(self):

        # set up searching for each crime defined in crime_keywords
        for crime_keyword in self.crime_keywords:
            print("processing crime: ", crime_keyword)
            gnews_parser = GnewsParser()
            gnews_parser.setup_search(crime_keyword, '2021-09-01', '2021-10-25')

            while True:
                res = gnews_parser.get_results()  # getting articles on daily basis

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

                    # break

                # break

    def parse(self, response, link, published, title, crime_keyword):
        item = GoogleNewsItem()  # this item will be writin in output file, when it is yield

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
