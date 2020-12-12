from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
import datetime
import logging
import os
import requests
import time


class PageLoader:
    def __init__(self, posts_count):
        self.post_divs_selector = 'div.rpBJOHq2PR60pnwJlUyP0 > div'
        self.page_posts_count = posts_count + posts_count // 2

    def __call__(self, driver):
        self.scroll_down_page(driver)
        post_divs_loaded = driver.find_elements_by_css_selector(self.post_divs_selector)
        if len(post_divs_loaded) > self.page_posts_count:
            return True
        else:
            return

    @staticmethod
    def scroll_down_page(driver):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")


class PostsGetter:
    def __init__(self, url, posts_count):
        self.driver = webdriver.Chrome()
        self.posts_query = ['div', {'class': '_1oQyIsiPHYt6nx7VOmd1sz'}]
        self.url = url
        self.posts_count = posts_count
        self.wait_seconds = 30

    def __enter__(self):
        self.driver.get(self.url)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.driver.quit()
        return True

    def get_posts(self):
        all_posts = []
        try:
            WebDriverWait(self.driver, self.wait_seconds).until(PageLoader(self.posts_count))
            page_text = self.driver.page_source
            page_text_soup = BeautifulSoup(page_text, features="html.parser")
            all_posts = page_text_soup.findAll(self.posts_query[0], self.posts_query[1])
        finally:
            return all_posts


class ParserError(Exception):
    def __init__(self, text, post_url=None):
        self.text = text
        self.post_url = post_url


class PostDataParser:
    def __init__(self, post):
        self.category_query = ['a', {"class": "_3ryJoIoycVkA88fy40qNJc"}]
        self.comments_count_query1 = ['span', {"class": "D6SuXeSnAAagG8dKAb4O4"}]
        self.comments_count_query2 = ['span', {"class": "FHCV02u6Cp2zYL0fhQPsO"}]
        self.date_and_url_query = ['a', {"class": "_3jOxDPIQ0KaOWpzvSQo-1s"}]
        self.karma_and_cake_day_query = ['span', {"class": "_1hNyZSklmcC7R_IfCUcXmZ"}]
        self.post_and_comment_karma_query = ['span', {"class": "karma"}]
        self.votes_count_query = ['div', {"class": "_1rZYMD_4xY3gRcSS3p8ODO"}]
        self.username_query = ['a', {"class": "_2tbHP6ZydRpjI44J3syuqC"}]
        self.post = str(post)
        self.post_soup = BeautifulSoup(self.post, features="html.parser")
        self.post_dict = {}
        self.methods_order = ['define_url_date', 'define_username_karmas_cakeday', 'define_comments_count',
                              'define_votes_count', 'define_category']
        self.dict_order = ['post_url', 'username', 'user_karma', 'user_cake_day', 'post_karma', 'comment_karma',
                           'post_date', 'comments_count', 'votes_count', 'post_category']
        self.extract_data()
        self.make_post_dict()

    def extract_data(self):
        for method_name in self.methods_order:
            getattr(self, method_name)()

    def define_url_date(self):
        try:
            date_and_url_tag = self.post_soup.findAll(self.date_and_url_query[0], self.date_and_url_query[1])[0]
        except IndexError:
            raise ParserError('Parser index error')
        self.post_url = date_and_url_tag.attrs["href"]
        self.post_date = self.convert_date(date_and_url_tag.text)

    def define_username_karmas_cakeday(self):
        try:
            user_tag = self.post_soup.findAll(self.username_query[0], self.username_query[1])[0]
        except IndexError:
            raise ParserError("User doesn't exist", self.post_url)
        self.username = user_tag.text[2:]
        user_profile_link_old = "https://old.reddit.com" + user_tag.attrs["href"]
        user_profile_link_new = "https://www.reddit.com" + user_tag.attrs["href"]
        user_page_text_old = self.get_html(user_profile_link_old)
        user_page_text_new = self.get_html(user_profile_link_new)

        page_text_soup = BeautifulSoup(user_page_text_old, features="html.parser")
        karma_tags = page_text_soup.findAll(self.post_and_comment_karma_query[0], self.post_and_comment_karma_query[1])
        if not karma_tags:
            raise ParserError("Page inaccessible to minors", self.post_url)
        page_text_soup = BeautifulSoup(user_page_text_new, features="html.parser")
        karma_and_cake_tags = page_text_soup.findAll(self.karma_and_cake_day_query[0], self.karma_and_cake_day_query[1])
        self.post_karma = karma_tags[0].text
        self.comment_karma = karma_tags[1].text
        self.user_karma = karma_and_cake_tags[0].text
        self.user_cake_day = karma_and_cake_tags[1].text

    def define_comments_count(self):
        comments_count_tags = self.post_soup.findAll(self.comments_count_query1[0], self.comments_count_query1[1])
        if comments_count_tags:
            comments_count_tag = comments_count_tags[0]
            self.comments_count = comments_count_tag.text
        else:
            comments_count_tag = self.post_soup.findAll(self.comments_count_query2[0], self.comments_count_query2[1])[0]
            raw_text = comments_count_tag.text
            space_index = raw_text.find(' ')
            self.comments_count = raw_text[:space_index]

    def define_votes_count(self):
        votes_count_tag = self.post_soup.findAll(self.votes_count_query[0], self.votes_count_query[1])[1]
        self.votes_count = votes_count_tag.text

    def define_category(self):
        category_tag = self.post_soup.findAll(self.category_query[0], self.category_query[1])[1]
        self.post_category = category_tag.text[2:]

    def make_post_dict(self):
        for attr_name in self.dict_order:
            self.post_dict[attr_name] = getattr(self, attr_name)

    @staticmethod
    def convert_date(date_str):
        if 'just now' in date_str or 'hour' in date_str:
            days = 0
        elif 'month' in date_str:
            days = 31
        else:
            days = int(date_str.split()[0])
        date = datetime.datetime.today() - datetime.timedelta(days=days)
        return date.strftime("%d.%m.%Y")

    @staticmethod
    def get_html(url):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:45.0) Gecko/20100101 Firefox/45.0'
        }
        request_succeed = False
        while not request_succeed:
            try:
                response = requests.get(url, timeout=5, headers=headers)
                request_succeed = True
            except requests.exceptions.ReadTimeout:
                time.sleep(1)
        response.encoding = 'utf8'
        return response.text


class FileWriter:
    def __init__(self, post_data):
        self.file_path = self.define_file_path()
        self.post_data = post_data

    def write_to_file(self):
        with open(self.file_path, 'w') as file:
            for post_dict in self.post_data:
                post_data_str = ''
                for data_name in post_dict:
                    data_value = post_dict[data_name]
                    post_data_str += f'{data_value}; '
                post_data_str = post_data_str[:len(post_data_str) - 2]
                file.write(post_data_str + '\n')

    @staticmethod
    def define_file_path():
        work_dir_path = os.getcwd()
        datetime_now = datetime.datetime.now()
        datetime_str = datetime_now.strftime("%Y%m%d%H%M")
        file_name = f'reddit-{datetime_str}.txt'
        return os.path.join(work_dir_path, file_name)


class PostsProcessor:
    def __init__(self, url, posts_count):
        self.url = url
        self.posts_count = posts_count
        self.all_posts = self.get_posts_list(self.url, self.posts_count)
        self.parsed_post_data = self.establish_post_data()
        FileWriter(self.parsed_post_data).write_to_file()

    def get_posts_list(self, url, posts_count):
        logging.basicConfig(filename="parserErrors.log", level=logging.INFO,
                            format='%(asctime)s. %(levelname)s: %(message)s')
        logging.info('Start sending requests')
        with PostsGetter(url, posts_count) as pg:
            return pg.get_posts()

    def establish_post_data(self):
        parsed_post_data = []
        for post in self.all_posts:
            if len(parsed_post_data) == self.posts_count:
                break
            try:
                post_dict = PostDataParser(post).post_dict
            except ParserError as err:
                logging.error(f'{err.text}, post URL: {err.post_url}')
                continue
            parsed_post_data.append(post_dict)
        logging.info('Stop sending requests')
        return parsed_post_data


PostsProcessor("https://www.reddit.com/top/?t=month", 100)
