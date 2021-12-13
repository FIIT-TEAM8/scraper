import feedparser
from datetime import datetime, timedelta
import json


class GnewsParser:
    __BASE_URL = "https://news.google.com/rss/search?q=<QUERY><DATERANGE><LOCALE>"
    __DATE_RANGE = "+after:<AFTER>+before:<BEFORE>"
    __LOCALE = {
        "sk": "&hl=sk&gl=SK&ceid=SK:sk",
        "en-us": "&hl=en-US&gl=US&ceid=US:en",
        "en-gb": "&hl=en-GB&gl=GB&ceid=GB:en"
    }

    def __init__(self):
        self.__url = GnewsParser.__BASE_URL
        self.__last_used_url = self.__url
        self.__start_date = None
        self.__end_date = None
        self.__current_window = None
        self.__locale = None
        self.__query = None
        self.__days_step = 1

    def setup_search(self, query, from_date, to_date, days_step=1, locale="en-us"):
        self.__setup_base_url(query, locale)
        self.__start_date = datetime.strptime(from_date, "%Y-%m-%d")
        self.__end_date = datetime.strptime(to_date, "%Y-%m-%d")
        self.__current_window = self.__start_date
        self.__days_step = days_step
        self.__locale = locale
        self.__query = query

    def __setup_base_url(self, query, locale):
        self.__url = self.__url.replace("<QUERY>", self.__get_clean_query(query))
        self.__url = self.__url.replace("<DATERANGE>", GnewsParser.__DATE_RANGE)
        self.__url = self.__url.replace("<LOCALE>", GnewsParser.__LOCALE[locale])

    def __get_clean_query(self, query):
        return query.replace(" ", "%20")

    def get_results(self):
        if self.__current_window + timedelta(days=self.__days_step) > self.__end_date:
            return None
        time_from = self.__current_window.strftime("%Y-%m-%d")
        new_url = self.__url
        new_url = new_url.replace("<AFTER>", time_from)
        self.__current_window += timedelta(days=self.__days_step)
        time_to = self.__current_window.strftime("%Y-%m-%d")
        new_url = new_url.replace("<BEFORE>", time_to)

        res = feedparser.parse(new_url)
        self.__last_used_url = new_url
        if res["status"] != 200:
            print(res["status"])
            return None
        return res["entries"]

    def save_state(self):
        save = {
            "last_url": self.__last_used_url,
            "search_from": self.__start_date.strftime("%Y-%m-%d"),
            "search_to": self.__end_date.strftime("%Y-%m-%d"),
            "current_window_date": self.__current_window.strftime("%Y-%m-%d"),
            "days_step": self.__days_step,
            "locale": self.__locale,
            "query": self.__query
        }
        return save

    def setup_search_from_state(self, save_file):
        f = open(save_file, "r")
        save = json.load(f)
        self.__last_used_url = save["last_url"]
        self.__start_date = datetime.strptime(save["search_from"], "%Y-%m-%d")
        self.__end_date = datetime.strptime(save["search_to"], "%Y-%m-%d")
        self.__current_window = datetime.strptime(save["current_window"], "%Y-%m-%d")
        self.__days_step = save["days_step"]
        self.__locale = save["locale"]
        self.__query = save["query"]
        self.__setup_base_url(self.__query, self.__locale)
