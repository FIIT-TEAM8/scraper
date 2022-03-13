from os.path import dirname
from database import Database
from elastic import Elastic
import os
import scrapy
from gnewsparser import GnewsParser
from google_news.items import GoogleNewsItem
from scrapy import Selector



CRIMES_FOLDER = './crimes/'

# run with command: scrapy crawl spider -o <outputfile.json>
# working directory: C:\Users\jakub\team_project\scraper\google_news\google_news

def get_text_content(html):
    final_html = ""

    try:
        # select only paragraphs and headings using xpath
        text_results = Selector(text=html).xpath('//p | //h1 | //h2 | //h3 | //h4 | //h5 | //h6').getall()
    except:
        return final_html

    # for each result (paragraph or heading tag) remove
    # all specifications - classes, ids etc.    
    for result in text_results:
        i = result.index(">")
 
        if "<p" in result:
            result = result[:2] + result[i:]
            tag_content = result[3:-4]

        elif "<h" in result:
            result = result[:3] + result[i:]
            tag_content = result[4:-5]

        # check if the body of current tag is empty
        # if it is, then ignore the tag
        if not tag_content.strip():
            continue

        result = str(result)
        final_html += result

    return final_html


class Spider(scrapy.Spider):
    name = "news_spider"

    __ERROR_MESSAGE = """
        Please provide arguments. Example:
        scrapy crawl {spider_name} -a crimes_file=FILE -a search_from=DATE -a search_to=DATE -a locale=LOCALE
    """
    def __load_crimes(self):
        results = []
        print(os.getcwd())
        for line in open(self.crimes_file, "r"):
            results.append(line.rstrip())
        return results



    def __init__(self, crimes_file="murder.txt", search_from="", search_to="", locale="",  **kwargs):
        super().__init__(**kwargs)
        if search_from == "" or search_to == "" or locale == "":
            print(self.__ERROR_MESSAGE)
            exit(1)
        self.crimes_file = CRIMES_FOLDER + crimes_file
        self.search_from = search_from
        self.search_to = search_to
        self.locale = locale
    

    def start_requests(self):
        loades_crimes = self.__load_crimes()

        # set up searching for each crime defined in crime_keywords
        for crime_keyword in loades_crimes:
            print("processing crime: ", crime_keyword)
            gnews_parser = GnewsParser()
            gnews_parser.setup_search(crime_keyword, self.search_from, self.search_to, locale=self.locale)
            
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
                                             loades_crimes=loades_crimes
                                            ),
                                         meta={
                                             'handle_httpstatus_all': True,
                                             'dont_retry': True,
                                         },
                                         )
                    # break

                # break

    def parse(self, response, link, published, title, crime_keyword , loaded_crimes):
        item = GoogleNewsItem()  # this item will be writin in output file, when it is yield
        Database.initialize()    # connect to mongo database
        Elastic.initialize() # connect to elasticsearch

        # parse only responses with status code 200
        if response.status == 200:
            try:
                # retrieve body tag with data
                body_tag = response.css('body').get()
                # retrieve only text tags from html body (paragraphs and headings)
                text_content = get_text_content(body_tag)

                # insert to database or update crime keywords
                Database.update('crimemaps', link, crime_keyword)

                # writes data into item, which will be yield into MongoDB pipeline
                item['title'] = title,
                item['published'] = published,
                item['link'] = link,
                item['html'] = text_content
                item['locale'] = self.locale

                yield item

            except Exception:
                # if page doesn't contains body tag, program will execute this line of code
                pass

        # store respones with status code other than 200
        else:
            # insert to database or update crime keywords
            Database.update('errorlinks', link, crime_keyword)  