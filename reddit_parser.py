from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from utils import convert_time_lapse_to_date, define_path_to_webdriver, get_html, posts_list_is_ready_check, \
    produce_data_file
import logging
import math
import time
import threading
import uuid


class PageLoader:
    def __init__(self, posts_count):
        """Takes needed for writing to file posts count, increases this count by a factor of 1.5 times

        to ensure a sufficient number of suitable posts in the final sample.
        """
        MULTIPLIER = 1.5
        self.page_posts_count = math.ceil(posts_count * MULTIPLIER)
        self.POST_DIVS_SELECTOR = 'div.rpBJOHq2PR60pnwJlUyP0 > div'
        self.SCROLL_DOWN_SCRIPT = 'window.scrollTo(0, document.body.scrollHeight);'

    def __call__(self, driver):
        """Scrolls down the page unless loaded posts count is sufficient"""

        driver.execute_script(self.SCROLL_DOWN_SCRIPT)
        post_divs_loaded = driver.find_elements_by_css_selector(self.POST_DIVS_SELECTOR)
        if len(post_divs_loaded) > self.page_posts_count:
            return True
        return False


class PostsGetter:
    def __init__(self, url, posts_count):
        """Initializes Chrome webdriver, sets posts load waiting limit"""
        self.driver = webdriver.Chrome(executable_path=define_path_to_webdriver())
        self.posts_query = ['div', {'class': '_1oQyIsiPHYt6nx7VOmd1sz'}]
        self.TAG_INDEX = 0
        self.CLASS_INDEX = 1
        self.url = url
        self.posts_count = posts_count
        self.WAIT_SECONDS = 30

    def __enter__(self):
        """Opens suggested site in browser"""
        self.driver.get(self.url)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Closes browser, suppress any exception"""
        self.driver.quit()
        return True

    def get_posts(self):
        """After waiting for the page to be loaded, finds all the posts presented on the page and

        returns them in a quantity that does not exceed needed post count triple.
        """
        all_posts = []
        try:
            WebDriverWait(self.driver, self.WAIT_SECONDS).until(PageLoader(self.posts_count))
            page_text = self.driver.page_source
            PARSER_NAME = 'html.parser'
            page_text_soup = BeautifulSoup(page_text, features=PARSER_NAME)
            all_posts = page_text_soup.findAll(self.posts_query[self.TAG_INDEX], self.posts_query[self.CLASS_INDEX])
        finally:
            MULTIPLIER = 3
            return all_posts[:self.posts_count * MULTIPLIER]


class ParserError(Exception):
    def __init__(self, text, post_index, post_url=None):
        """Takes error text, index and url of the post which raised the exception"""
        self.text = text
        self.post_index = post_index
        self.post_url = post_url


class PostDataParser:
    def __init__(self, post_index, post, posts_list):
        """Sets out queries for searching specific data in HTML and

        the order of calling methods and making dictionary.
        """
        self.category_query = ['a', {"class": "_3ryJoIoycVkA88fy40qNJc"}]
        self.comments_count_query1 = ['span', {"class": "D6SuXeSnAAagG8dKAb4O4"}]
        self.comments_count_query2 = ['span', {"class": "FHCV02u6Cp2zYL0fhQPsO"}]
        self.date_and_url_query = ['a', {"class": "_3jOxDPIQ0KaOWpzvSQo-1s"}]
        self.karma_and_cake_day_query = ['span', {"class": "_1hNyZSklmcC7R_IfCUcXmZ"}]
        self.post_and_comment_karma_query = ['span', {"class": "karma"}]
        self.votes_count_query = ['div', {"class": "_1rZYMD_4xY3gRcSS3p8ODO"}]
        self.username_query = ['a', {"class": "_2tbHP6ZydRpjI44J3syuqC"}]
        self.TAG_INDEX = 0
        self.CLASS_INDEX = 1
        self.post_index = post_index
        self.post = str(post)
        self.posts_list = posts_list
        self.post_soup = BeautifulSoup(self.post, features="html.parser")
        self.post_dict = {}
        self.unique_id = uuid.uuid1().hex
        self.methods_order = ['define_url_date', 'define_username_karmas_cakeday', 'define_comments_count',
                              'define_votes_count', 'define_category']
        self.dict_order = ['post_index', 'unique_id', 'post_url', 'username', 'user_karma', 'user_cake_day',
                           'post_karma', 'comment_karma', 'post_date', 'comments_count', 'votes_count', 'post_category']

    def add_post_data_to_list(self):
        """Generates post-related data, writes it to a dictionary, which is added to posts list.

        If Parser error occurred, logs it and writes index of the post which raised the exception to the dictionary.
        """
        try:
            for method_name in self.methods_order:
                getattr(self, method_name)()
            for attr_name in self.dict_order:
                self.post_dict[attr_name] = getattr(self, attr_name)
        except ParserError as err:
            logging.error(f'{err.text}, post URL: {err.post_url}')
            POST_ORDER_INDEX_KEY = 'post_index'
            self.post_dict = {POST_ORDER_INDEX_KEY: err.post_index}
        self.posts_list.append(self.post_dict)

    def define_url_date(self):
        """Defines post URL and post date, suppresses IndexError that could be thrown if tag isn't found"""
        try:
            NEEDED_RESULT_INDEX = 0
            date_and_url_tag = self.post_soup.findAll(self.date_and_url_query[self.TAG_INDEX],
                                                      self.date_and_url_query[self.CLASS_INDEX])[NEEDED_RESULT_INDEX]
        except IndexError:
            ERROR_TEXT = 'Parser index error'
            raise ParserError(ERROR_TEXT, self.post_index)
        ATTRIBUTE_NAME = 'href'
        self.post_url = date_and_url_tag.attrs[ATTRIBUTE_NAME]
        self.post_date = convert_time_lapse_to_date(date_and_url_tag.text)

    def define_username_karmas_cakeday(self):
        """Tries to find post creator at first. In case the user is deleted relevant exception is thrown.

        If not, makes a request to the old version of the site to defines post and comment karma,
        and the request to the new version of the site to define user karma and user cake day.
        If user's private page is inaccessible to minors, relevant exception is thrown.
        """
        try:
            NEEDED_RESULT_INDEX = 0
            user_tag = self.post_soup.findAll(self.username_query[self.TAG_INDEX],
                                              self.username_query[self.CLASS_INDEX])[NEEDED_RESULT_INDEX]
        except IndexError:
            ERROR_TEXT = "User doesn't exist"
            raise ParserError(ERROR_TEXT, self.post_index, self.post_url)
        USERNAME_START_INDEX = 2
        self.username = user_tag.text[USERNAME_START_INDEX:]
        ATTRIBUTE_NAME = 'href'
        OLD_URL_PREFIX = "https://old.reddit.com"
        NEW_URL_PREFIX = "https://www.reddit.com"
        user_profile_link_old = f'{OLD_URL_PREFIX}{user_tag.attrs[ATTRIBUTE_NAME]}'
        user_profile_link_new = f'{NEW_URL_PREFIX}{user_tag.attrs[ATTRIBUTE_NAME]}'
        user_page_text_old = get_html(user_profile_link_old)
        user_page_text_new = get_html(user_profile_link_new)
        PARSER_NAME = 'html.parser'
        page_text_soup = BeautifulSoup(user_page_text_old, features=PARSER_NAME)
        karma_tags = page_text_soup.findAll(self.post_and_comment_karma_query[self.TAG_INDEX],
                                            self.post_and_comment_karma_query[self.CLASS_INDEX])
        if not karma_tags:
            ERROR_TEXT = 'Page inaccessible to minors'
            raise ParserError(ERROR_TEXT, self.post_index, self.post_url)
        page_text_soup = BeautifulSoup(user_page_text_new, features=PARSER_NAME)
        karma_and_cake_tags = page_text_soup.findAll(self.karma_and_cake_day_query[self.TAG_INDEX],
                                                     self.karma_and_cake_day_query[self.CLASS_INDEX])
        POST_KARMA_INDEX = 0
        COMMENT_KARMA_INDEX = 1
        USER_KARMA_INDEX = 0
        USER_CAKE_DAY_INDEX = 1
        self.post_karma = karma_tags[POST_KARMA_INDEX].text
        self.comment_karma = karma_tags[COMMENT_KARMA_INDEX].text
        self.user_karma = karma_and_cake_tags[USER_KARMA_INDEX].text
        self.user_cake_day = karma_and_cake_tags[USER_CAKE_DAY_INDEX].text

    def define_comments_count(self):
        """Defines number of comments. If initial query doesn't deliver a result, the second will be used for search."""
        comments_tags = self.post_soup.findAll(self.comments_count_query1[self.TAG_INDEX],
                                               self.comments_count_query1[self.CLASS_INDEX])
        NEEDED_RESULT_INDEX = 0
        if comments_tags:
            comments_tag = comments_tags[NEEDED_RESULT_INDEX]
            self.comments_count = comments_tag.text
        else:
            comments_tag = self.post_soup.findAll(self.comments_count_query2[self.TAG_INDEX],
                                                  self.comments_count_query2[self.CLASS_INDEX])[NEEDED_RESULT_INDEX]
            raw_text = comments_tag.text
            space_index = raw_text.find(' ')
            self.comments_count = raw_text[:space_index]

    def define_votes_count(self):
        """Defines number of votes"""
        NEEDED_RESULT_INDEX = 1
        votes_count_tag = self.post_soup.findAll(self.votes_count_query[self.TAG_INDEX],
                                                 self.votes_count_query[self.CLASS_INDEX])[NEEDED_RESULT_INDEX]
        self.votes_count = votes_count_tag.text

    def define_category(self):
        """Defines post category"""
        NEEDED_RESULT_INDEX = 1
        category_tag = self.post_soup.findAll(self.category_query[self.TAG_INDEX],
                                              self.category_query[self.CLASS_INDEX])[NEEDED_RESULT_INDEX]
        POST_CATEGORY_START_INDEX = 2
        self.post_category = category_tag.text[POST_CATEGORY_START_INDEX:]


class PostsProcessor:
    def __init__(self, url, posts_count):
        """Takes URL from reddit.com and count of posts which have to be written to output file.

        Forms a list of all posts in HTML format presented on the webpage.
        Parses these data and make a list of each post data from them.
        Writes stringified post data to the file.
        Logs information about program life-cycle process.
        """
        self.url = url
        self.posts_count = posts_count
        self.all_posts = self.get_posts_list(self.url, self.posts_count)
        logging.info('Stop running Chrome webdriver')
        self.parsed_posts_data = self.establish_post_data()
        produce_data_file(self.parsed_posts_data)

    def get_posts_list(self, url, posts_count):
        """Tries to find posts on indicated URL in a certain amount exceeding required to be written to the file.

        Does basic configuration for the logging system, logs information about starting of running Chrome webdriver.
        """
        logging.basicConfig(filename="programLogs.log", level=logging.INFO,
                            format='%(asctime)s. %(levelname)s: %(message)s')
        logging.info('Start running Chrome webdriver')
        with PostsGetter(url, posts_count) as pg:
            return pg.get_posts()

    def establish_post_data(self):
        """Starts thread-team for parsing HTML format posts into dictionaries, which will be added to posts list.

        If order and count of the posts meeting the criteria corresponds to needed, stop thread-team.
        Logs the information about starting and finishing of sending requests.
        """
        posts_data = []
        logging.info('Start sending requests')
        for ind, post in enumerate(self.all_posts):
            threading.Thread(target=PostDataParser(ind, post, posts_data).add_post_data_to_list, daemon=True).start()
        MULTIPLIER = 0.2
        wait_before_start_check_seconds = self.posts_count * MULTIPLIER
        time.sleep(wait_before_start_check_seconds)
        WAIT_NEXT_CHECK_SECONDS = 0.5
        while True:
            if posts_list_is_ready_check(posts_data, self.posts_count, len(self.all_posts)):
                break
            time.sleep(WAIT_NEXT_CHECK_SECONDS)
        logging.info('Stop sending requests')
        POST_ORDER_INDEX_KEY = 'post_index'
        parsed_posts_data = sorted(posts_data[::], key=lambda post_dict: post_dict[POST_ORDER_INDEX_KEY])
        for post_dict in parsed_posts_data:
            del post_dict[POST_ORDER_INDEX_KEY]
        parsed_posts_data = [post_dict for post_dict in parsed_posts_data if post_dict][:self.posts_count]
        return parsed_posts_data


if __name__ == "__main__":
    PostsProcessor("https://www.reddit.com/top/?t=month", 100)
