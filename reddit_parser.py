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
        multiplier = 1.5
        self.page_posts_count = math.ceil(posts_count * multiplier)
        self.post_divs_selector = 'div.rpBJOHq2PR60pnwJlUyP0 > div'
        self.scroll_down_page = 'window.scrollTo(0, document.body.scrollHeight);'

    def __call__(self, driver):
        """Scrolls down the page unless loaded posts count is sufficient"""

        driver.execute_script(self.scroll_down_page)
        post_divs_loaded = driver.find_elements_by_css_selector(self.post_divs_selector)
        if len(post_divs_loaded) > self.page_posts_count:
            return True
        return False


class PostsGetter:
    def __init__(self, url, posts_count):
        """Initializes Chrome webdriver, sets posts load waiting limit"""
        self.driver = webdriver.Chrome(executable_path=define_path_to_webdriver())
        self.posts_query = ['div', {'class': '_1oQyIsiPHYt6nx7VOmd1sz'}]
        self.tag_index = 0
        self.class_index = 1
        self.url = url
        self.posts_count = posts_count
        self.wait_seconds = 30

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
            WebDriverWait(self.driver, self.wait_seconds).until(PageLoader(self.posts_count))
            page_text = self.driver.page_source
            parser_name = 'html.parser'
            page_text_soup = BeautifulSoup(page_text, features=parser_name)
            all_posts = page_text_soup.findAll(self.posts_query[self.tag_index], self.posts_query[self.class_index])
        finally:
            multiplier = 3
            return all_posts[:self.posts_count * multiplier]


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
        self.tag_index = 0
        self.class_index = 1
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
            post_order_index_key = 'post_index'
            self.post_dict = {post_order_index_key: err.post_index}
        self.posts_list.append(self.post_dict)

    def define_url_date(self):
        """Defines post URL and post date, suppresses IndexError that could be thrown if tag isn't found"""
        try:
            needed_result_index = 0
            date_and_url_tag = self.post_soup.findAll(self.date_and_url_query[self.tag_index],
                                                      self.date_and_url_query[self.class_index])[needed_result_index]
        except IndexError:
            error_text = 'Parser index error'
            raise ParserError(error_text, self.post_index)
        attribute_name = 'href'
        self.post_url = date_and_url_tag.attrs[attribute_name]
        self.post_date = convert_time_lapse_to_date(date_and_url_tag.text)

    def define_username_karmas_cakeday(self):
        """Tries to find post creator at first. In case the user is deleted relevant exception is thrown.

        If not, makes a request to the old version of the site to defines post and comment karma,
        and the request to the new version of the site to define user karma and user cake day.
        If user's private page is inaccessible to minors, relevant exception is thrown.
        """
        try:
            needed_result_index = 0
            user_tag = self.post_soup.findAll(self.username_query[self.tag_index],
                                              self.username_query[self.class_index])[needed_result_index]
        except IndexError:
            error_text = "User doesn't exist"
            raise ParserError(error_text, self.post_index, self.post_url)
        username_start_index = 2
        self.username = user_tag.text[username_start_index:]
        attribute_name = 'href'
        old_url_prefix = "https://old.reddit.com"
        new_url_prefix = "https://www.reddit.com"
        user_profile_link_old = f'{old_url_prefix}{user_tag.attrs[attribute_name]}'
        user_profile_link_new = f'{new_url_prefix}{user_tag.attrs[attribute_name]}'
        user_page_text_old = get_html(user_profile_link_old)
        user_page_text_new = get_html(user_profile_link_new)
        parser_name = 'html.parser'
        page_text_soup = BeautifulSoup(user_page_text_old, features=parser_name)
        karma_tags = page_text_soup.findAll(self.post_and_comment_karma_query[self.tag_index],
                                            self.post_and_comment_karma_query[self.class_index])
        if not karma_tags:
            error_text = 'Page inaccessible to minors'
            raise ParserError(error_text, self.post_index, self.post_url)
        page_text_soup = BeautifulSoup(user_page_text_new, features=parser_name)
        karma_and_cake_tags = page_text_soup.findAll(self.karma_and_cake_day_query[self.tag_index],
                                                     self.karma_and_cake_day_query[self.class_index])
        post_karma_index = 0
        comment_karma_index = 1
        user_karma_index = 0
        user_cake_day_index = 1
        self.post_karma = karma_tags[post_karma_index].text
        self.comment_karma = karma_tags[comment_karma_index].text
        self.user_karma = karma_and_cake_tags[user_karma_index].text
        self.user_cake_day = karma_and_cake_tags[user_cake_day_index].text

    def define_comments_count(self):
        """Defines number of comments. If initial query doesn't deliver a result, the second will be used for search."""
        comments_tags = self.post_soup.findAll(self.comments_count_query1[self.tag_index],
                                               self.comments_count_query1[self.class_index])
        needed_result_index = 0
        if comments_tags:
            comments_tag = comments_tags[needed_result_index]
            self.comments_count = comments_tag.text
        else:
            comments_tag = self.post_soup.findAll(self.comments_count_query2[self.tag_index],
                                                  self.comments_count_query2[self.class_index])[needed_result_index]
            raw_text = comments_tag.text
            space_index = raw_text.find(' ')
            self.comments_count = raw_text[:space_index]

    def define_votes_count(self):
        """Defines number of votes"""
        needed_result_index = 1
        votes_count_tag = self.post_soup.findAll(self.votes_count_query[self.tag_index],
                                                 self.votes_count_query[self.class_index])[needed_result_index]
        self.votes_count = votes_count_tag.text

    def define_category(self):
        """Defines post category"""
        needed_result_index = 1
        category_tag = self.post_soup.findAll(self.category_query[self.tag_index],
                                              self.category_query[self.class_index])[needed_result_index]
        post_category_start_index = 2
        self.post_category = category_tag.text[post_category_start_index:]


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
        multiplier = 0.2
        wait_before_start_check_seconds = self.posts_count * multiplier
        time.sleep(wait_before_start_check_seconds)
        wait_next_check_seconds = 0.5
        while True:
            if posts_list_is_ready_check(posts_data, self.posts_count, len(self.all_posts)):
                break
            time.sleep(wait_next_check_seconds)
        logging.info('Stop sending requests')
        post_order_index_key = 'post_index'
        parsed_posts_data = sorted(posts_data[::], key=lambda post_dict: post_dict[post_order_index_key])
        for post_dict in parsed_posts_data:
            del post_dict[post_order_index_key]
        parsed_posts_data = [post_dict for post_dict in parsed_posts_data if post_dict][:self.posts_count]
        return parsed_posts_data


if __name__ == "__main__":
    PostsProcessor("https://www.reddit.com/top/?t=month", 100)
