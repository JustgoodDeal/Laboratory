from bs4 import BeautifulSoup
from concurrent.futures import as_completed, ThreadPoolExecutor
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from utils import DataConverter, define_path_to_file, get_html
import datetime
import logging
import os
import uuid


class PageLoader:
    def __init__(self, posts_count):
        """Takes needed for writing to file posts count, increases this count by a factor of 1.5 times

        to ensure a sufficient number of suitable posts in the final sample.
        """
        self.post_divs_selector = 'div.rpBJOHq2PR60pnwJlUyP0 > div'
        self.page_posts_count = posts_count + posts_count // 2

    def __call__(self, driver):
        """Scrolls down the page unless loaded posts count is sufficient"""
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        post_divs_loaded = driver.find_elements_by_css_selector(self.post_divs_selector)
        if len(post_divs_loaded) > self.page_posts_count:
            return True
        else:
            return


class PostsGetter:
    def __init__(self, url, posts_count):
        """Initializes Chrome webdriver, sets posts load waiting limit"""
        self.driver = webdriver.Chrome(executable_path=self.define_path_to_webdriver())
        self.posts_query = ['div', {'class': '_1oQyIsiPHYt6nx7VOmd1sz'}]
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

    def define_path_to_webdriver(self):
        """Defines path to Chrome webdriver under config file"""
        config_dict = DataConverter.convert_data_from_yaml_to_dict()
        path_from_config = config_dict.get('executable_path')
        executable_path = path_from_config if path_from_config else 'chromedriver'
        return executable_path

    def get_posts(self):
        """After waiting for the page to be loaded, finds all the posts presented on the page and

        returns them in a quantity that does not exceed needed post count twice.
        """
        all_posts = []
        try:
            WebDriverWait(self.driver, self.wait_seconds).until(PageLoader(self.posts_count))
            page_text = self.driver.page_source
            page_text_soup = BeautifulSoup(page_text, features="html.parser")
            all_posts = page_text_soup.findAll(self.posts_query[0], self.posts_query[1])[:self.posts_count * 2]
        finally:
            return all_posts


class ParserError(Exception):
    def __init__(self, text, post_index, post_url=None):
        """Takes error text and post url which raised the exception"""
        self.text = text
        self.post_index = post_index
        self.post_url = post_url


class PostDataParser:
    def __init__(self, post_index, post):
        """Defines queries for searching specific data in HTML, extracts post-related data from HTML and

        write this data to dictionary.
        """
        self.category_query = ['a', {"class": "_3ryJoIoycVkA88fy40qNJc"}]
        self.comments_count_query1 = ['span', {"class": "D6SuXeSnAAagG8dKAb4O4"}]
        self.comments_count_query2 = ['span', {"class": "FHCV02u6Cp2zYL0fhQPsO"}]
        self.date_and_url_query = ['a', {"class": "_3jOxDPIQ0KaOWpzvSQo-1s"}]
        self.karma_and_cake_day_query = ['span', {"class": "_1hNyZSklmcC7R_IfCUcXmZ"}]
        self.post_and_comment_karma_query = ['span', {"class": "karma"}]
        self.votes_count_query = ['div', {"class": "_1rZYMD_4xY3gRcSS3p8ODO"}]
        self.username_query = ['a', {"class": "_2tbHP6ZydRpjI44J3syuqC"}]
        self.post_index = post_index
        self.post = str(post)
        self.post_soup = BeautifulSoup(self.post, features="html.parser")
        self.post_dict = {}
        self.unique_id = uuid.uuid1().hex
        self.methods_order = ['define_url_date', 'define_username_karmas_cakeday', 'define_comments_count',
                              'define_votes_count', 'define_category']
        self.dict_order = ['post_index', 'unique_id', 'post_url', 'username', 'user_karma', 'user_cake_day',
                           'post_karma', 'comment_karma', 'post_date', 'comments_count', 'votes_count', 'post_category']

    def make_post_dict(self):
        """Generates post-related data and writes it to dictionary according to a certain order"""
        for method_name in self.methods_order:
            getattr(self, method_name)()
        for attr_name in self.dict_order:
            self.post_dict[attr_name] = getattr(self, attr_name)
        return self.post_dict

    def define_url_date(self):
        """Defines post URL and post date, suppresses IndexError that could be thrown if tag isn't found"""
        try:
            date_and_url_tag = self.post_soup.findAll(self.date_and_url_query[0], self.date_and_url_query[1])[0]
        except IndexError:
            raise ParserError('Parser index error', self.post_index)
        self.post_url = date_and_url_tag.attrs["href"]
        self.post_date = DataConverter.convert_time_lapse_to_date(date_and_url_tag.text)

    def define_username_karmas_cakeday(self):
        """Tries to find post creator at first. In case the user is deleted relevant exception is thrown.

        If not, makes a request to the old version of the site to defines post and comment karma,
        and the request to the new version of the site to define user karma and user cake day.
        If user's private page is inaccessible to minors, relevant exception is thrown.
        """
        try:
            user_tag = self.post_soup.findAll(self.username_query[0], self.username_query[1])[0]
        except IndexError:
            raise ParserError("User doesn't exist", self.post_index, self.post_url)
        self.username = user_tag.text[2:]
        user_profile_link_old = "https://old.reddit.com" + user_tag.attrs["href"]
        user_profile_link_new = "https://www.reddit.com" + user_tag.attrs["href"]
        user_page_text_old = get_html(user_profile_link_old)
        user_page_text_new = get_html(user_profile_link_new)

        page_text_soup = BeautifulSoup(user_page_text_old, features="html.parser")
        karma_tags = page_text_soup.findAll(self.post_and_comment_karma_query[0], self.post_and_comment_karma_query[1])
        if not karma_tags:
            raise ParserError("Page inaccessible to minors", self.post_index, self.post_url)
        page_text_soup = BeautifulSoup(user_page_text_new, features="html.parser")
        karma_and_cake_tags = page_text_soup.findAll(self.karma_and_cake_day_query[0], self.karma_and_cake_day_query[1])
        self.post_karma = karma_tags[0].text
        self.comment_karma = karma_tags[1].text
        self.user_karma = karma_and_cake_tags[0].text
        self.user_cake_day = karma_and_cake_tags[1].text

    def define_comments_count(self):
        """Defines number of comments. If initial query doesn't deliver a result, the second will be used for search."""
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
        """Defines number of votes"""
        votes_count_tag = self.post_soup.findAll(self.votes_count_query[0], self.votes_count_query[1])[1]
        self.votes_count = votes_count_tag.text

    def define_category(self):
        """Defines post category"""
        category_tag = self.post_soup.findAll(self.category_query[0], self.category_query[1])[1]
        self.post_category = category_tag.text[2:]


class FileWriter:
    def __init__(self, post_data):
        """Takes a list with collected data from all posts. Defines the path to output file,

        writes stringified post data to it after having removed previous one if existing.
        """
        self.post_data = post_data
        self.new_file_name = self.define_file_name('txt')
        self.path_to_new_file = os.path.join(os.getcwd(), self.new_file_name)
        self.remove_old_file()
        self.write_data_to_new_file()

    def write_data_to_new_file(self):
        """Writes post data stringified from dictionary to the new file"""
        with open(self.path_to_new_file, 'w') as file:
            for ind, post_dict in enumerate(self.post_data):
                post_data_str = DataConverter.make_str_from_dict(post_dict)
                if ind != len(self.post_data) - 1:
                    post_data_str += '\n'
                file.write(post_data_str)

    def remove_old_file(self):
        """Removes no longer needed post data file if existing"""
        path_to_old_file = define_path_to_file('reddit-')
        if path_to_old_file:
            os.remove(path_to_old_file)

    def define_file_name(self, file_format):
        """Defines the name of output file based on the file format and current time"""
        datetime_now = datetime.datetime.now()
        datetime_str = datetime_now.strftime("%Y%m%d%H%M")
        file_name = f'reddit-{datetime_str}.{file_format}'
        return file_name


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
        FileWriter(self.parsed_posts_data)

    def get_posts_list(self, url, posts_count):
        """Tries to find posts on indicated URL in the amount by a factor

        of 1.5 times exceeding required to be written to the file.
        Does basic configuration for the logging system,
        logs information about starting of running Chrome webdriver.
        """
        logging.basicConfig(filename="parserLogs.log", level=logging.INFO,
                            format='%(asctime)s. %(levelname)s: %(message)s')
        logging.info('Start running Chrome webdriver')
        with PostsGetter(url, posts_count) as pg:
            return pg.get_posts()

    def establish_post_data(self):
        """Starts thread-team for parsing HTML format posts into dictionaries, which are added to a list.

        If the count of added posts is equal to needed, stop thread-team.
        Logs Parser errors and information about finishing of sending requests.
        """
        parsed_posts_data = []
        with ThreadPoolExecutor() as executor:
            futures = []
            logging.info('Start sending requests')
            for post_index, post in enumerate(self.all_posts):
                futures.append(executor.submit(PostDataParser(post_index, post).make_post_dict))
            exceptions_count = 0
            for future in as_completed(futures):
                needed_posts_count = self.posts_count + exceptions_count
                if len(parsed_posts_data) >= needed_posts_count:
                    latest_needed_post_index = parsed_posts_data[needed_posts_count - 1]['post_index']
                    if latest_needed_post_index == needed_posts_count - 1:
                        break
                try:
                    parsed_posts_data.append(future.result())
                    parsed_posts_data = sorted(parsed_posts_data, key=lambda post_dict: post_dict['post_index'])
                except ParserError as err:
                    logging.error(f'{err.text}, post URL: {err.post_url}')
                    parsed_posts_data.append({'post_index': err.post_index})
                    exceptions_count += 1
                    continue
            logging.info('Stop sending requests')
            [post_dict.pop('post_index') for post_dict in parsed_posts_data]
            parsed_posts_data = [post_dict for post_dict in parsed_posts_data if post_dict][:self.posts_count]
        return parsed_posts_data


if __name__ == "__main__":
    PostsProcessor("https://www.reddit.com/top/?t=month", 100)
