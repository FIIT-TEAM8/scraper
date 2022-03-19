from os.path import dirname
from database import Database
from elastic import Elastic
import os
import scrapy
from gnewsparser import GnewsParser
from google_news.items import GoogleNewsItem
from scrapy import Selector
import logging



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
        ''' 
            open list_of_crimes_english and user specified file with list of crimes in other language english too
            create and return dictionary where key value is crime keyword from user specified file and value is corresponding english crime keyword 
        '''

        crimes_dict:dict = {}

        crime_f = open(self.crimes_file, "r", encoding="utf8")
        crime_f_en = open(self.crimes_file_en, "r", encoding="utf8")

        crime_lines:list[str] = [line.replace("\n", "") for line in crime_f.readlines()]
        crime_lines_en:list[str] = [line.replace("\n", "") for line in crime_f_en.readlines()]

        crimes_dict:dict = {crime_keyword: crime_keyword_en for crime_keyword, crime_keyword_en in zip(crime_lines, crime_lines_en)}

        crime_f_en.close()
        crime_f.close()

        return crimes_dict

    def process_locale(self, locale):
        region = locale
        language = locale

        if '-' in locale:
            region = locale.split('-')[1]
            language = locale.split('-')[0]

        return region, language


    def __init__(self, crimes_file="murder.txt", search_from="", search_to="", locale="", days_step=1,  **kwargs):
        super().__init__(**kwargs)
        if search_from == "" or search_to == "" or locale == "":
            logging.error(self.__ERROR_MESSAGE)
            exit(1)
        self.crimes_file = CRIMES_FOLDER + crimes_file
        self.crimes_file_en = CRIMES_FOLDER + 'list_of_crimes_english.txt'
        self.search_from = search_from
        self.search_to = search_to
        self.locale = locale
        self.days_step = days_step
    

    def start_requests(self):
        loaded_crimes_dict = self.__load_crimes()

        # set up searching for each crime defined in crime_keywords
        for crime_keyword, crime_keyword_en in loaded_crimes_dict.items():
            print("processing crime: ", crime_keyword)
            gnews_parser = GnewsParser()
            gnews_parser.setup_search(crime_keyword, self.search_from, self.search_to, locale=self.locale, days_step=self.days_step)
            
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
                                             crime_keyword=crime_keyword,
                                             crime_keyword_en=crime_keyword_en,
                                             loaded_crimes_dict=loaded_crimes_dict
                                            ),
                                         meta={
                                             'handle_httpstatus_all': True,
                                             'dont_retry': True,
                                         },
                                         )
                                         

    def parse(self, response, link, published, title, crime_keyword, crime_keyword_en, loaded_crimes_dict):
        item = GoogleNewsItem()  # this item will be writin in output file, when it is yield
        Database.initialize()    # connect to mongo database
        Elastic.initialize()     # connect to elasticsearch

        # parse only responses with status code 200
        if response.status == 200:
            try:
                # retrieve body tag with data
                body_tag = response.css('body').get()
                # retrieve only text tags from html body (paragraphs and headings)
                text_content = get_text_content(body_tag)

                # lower case text context for crimes keywords searching
                text_content_lower = text_content.lower()

                # all crime keywords, which are in article's text will be in this list
                # crime keywords will be in english for better consistency, when searching an article from multiple countries based on crime keyword
                crimes_in_article = [crime_keyword_en]

                # iterate through each keyword and check if it is in article
                for keyword_crime, keyword_crime_en in loaded_crimes_dict.items():
                    # arleady contains this crime
                    if keyword_crime == crime_keyword:
                        continue
                    
                    # lower case keyword_crime before adding spaces
                    # to find out if keyword_crime is single word add blank space before and after keyword_crime
                    # this makes sure, that only whole words are matched and not substrings of words. example: 'word' in 'swordsmith' == True, but ' word ' in 'swordsmith' == False
                    keyword_crime_spaces = ' ' + keyword_crime.lower() + ' '

                    if keyword_crime_spaces in text_content_lower:
                        print('UPDATED CRIME {} FOR LINK {}'.format(keyword_crime, link))
                        # add english crime keyword to list, which will be stored in keywords field in MongoDB
                        crimes_in_article.append(keyword_crime_en)

                # writes data into item, which will be yield into MongoDB pipeline
                item['title'] = title,
                item['published'] = published,
                item['link'] = link,
                item['html'] = text_content
                item['keywords'] = crimes_in_article

                # '-' in locale makes sure, there is language and region, otherwise only language is passed https://developers.google.com/search/docs/advanced/crawling/localized-versions#regional-variations-table
                if '-' in self.locale:
                    region, language = self.process_locale(self.locale)
                    item['region'] = region
                    item['language'] = language
                else:
                    # possible languages https://developers.google.com/admin-sdk/directory/v1/languages
                    item['language'] = self.locale

                yield item

            except Exception:
                # if page doesn't contains body tag, program will execute this line of code
                pass

        # store respones with status code other than 200
        else:
            # insert to database or update crime keywords
            Database.update('errorlinks', link, crime_keyword)  