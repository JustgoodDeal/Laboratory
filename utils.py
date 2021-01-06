import datetime
import logging
import time
import requests
import yaml


class DataConverter:
    @staticmethod
    def make_dict_from_tuple(tup):
        """Converts post data obtained from a database to dictionary in a specific sequence

        If data is a datetime object, converts it to a string"""
        dict_order_map = {
            'unique_id': '', 'post_url': '', 'username': '', 'user_karma': '', 'user_cake_day': 'datetime',
            'post_karma': '', 'comment_karma': '', 'post_date': 'datetime', 'comments_number': '',
            'votes_number': '', 'post_category': ''
        }
        post_dict = {}
        ind = 0
        for name in dict_order_map:
            value = tup[ind]
            value_type = dict_order_map[name]
            if value_type == 'datetime':
                value = value.strftime("%d.%m.%Y")
            post_dict[name] = value
            ind += 1
        return post_dict

    @staticmethod
    def convert_time_lapse_to_date(date_str):
        """Takes a string containing time lapse between publishing post and current time.

        ('just now', '7 days ago', '1 month ago', etc.). Converts it to the date when the post was published.
        """
        if 'just now' in date_str or 'hour' in date_str:
            days = 0
        elif 'month' in date_str:
            days = 31
        else:
            days = int(date_str.split()[0])
        date = datetime.datetime.today() - datetime.timedelta(days=days)
        return date.strftime("%m.%d.%Y")

    @staticmethod
    def convert_date(post_dict, format):
        """Converts string representation of specific dates from post dict to indicated format.

        If month is given as a format, day and month switch places; otherwise,
        if day and month are one-digit numbers, zero is placed before them.
        """
        format = "%m.%d.%Y" if format == 'month' else "%d.%m.%Y"
        for name in post_dict:
            if name in {'user_cake_day', 'post_date'}:
                try:
                    inverted_date = datetime.datetime.strptime(post_dict.get(name), '%d.%m.%Y').strftime(format)
                    post_dict[name] = inverted_date
                except ValueError:
                    ...
        return post_dict

    @staticmethod
    def convert_data_from_yaml_to_dict():
        """Tries to convert data from config file in yaml format to dictionary. If the config file contains
        data which couldn't be converted to dictionary or yaml file doesn't exist, returns empty dictionary.
        """
        config_dict = {}
        try:
            with open("config.yaml") as file:
                config_dict = yaml.safe_load(file)
                if not type(config_dict) is dict:
                    config_dict = {}
        except FileNotFoundError:
            ...
        return config_dict


def posts_list_is_ready_check(posts_list, needed_posts_count, stop_count):
    """Checks whether order and count of the posts meeting the criteria corresponds to needed"""
    if len(posts_list) == stop_count:
        return True
    posts_list_copy = posts_list.copy()
    if len(posts_list) >= needed_posts_count:
        posts_list_copy = sorted(posts_list_copy, key=lambda post_dict: post_dict['post_index'])
        init_list_slice = posts_list_copy[:needed_posts_count]
        right_posts_order = init_list_slice[len(init_list_slice) - 1]['post_index'] == needed_posts_count - 1
        if right_posts_order:
            unsuitable_posts_count = len([post_dict for post_dict in init_list_slice if len(post_dict) == 1])
            if needed_posts_count + unsuitable_posts_count == len(init_list_slice):
                return True
            for post_dict_index in range(needed_posts_count, len(posts_list_copy)):
                current_post_dict = posts_list_copy[post_dict_index]
                right_posts_order = current_post_dict['post_index'] == post_dict_index
                if right_posts_order:
                    if len(current_post_dict) == 1:
                        unsuitable_posts_count += 1
                        continue
                    further_list_slice = posts_list_copy[:post_dict_index + 1]
                    if needed_posts_count + unsuitable_posts_count == len(further_list_slice):
                        return True


def define_connection_entries(default_connection_entries):
    """Defines connection entries under config file. If any of the entry isn't specified

    in the config file, default value is set for this entry.
    """
    config_dict = DataConverter.convert_data_from_yaml_to_dict()
    conn_entries = {}
    for entry in default_connection_entries:
        conn_entries[entry] = config_dict.get(entry) or default_connection_entries[entry]
    return conn_entries


def get_html(url):
    """Sends a request to indicated URL and return server response text in HTML format.

    In case of ReadTimeout or Connection error, logs it, suspends execution of a program
    for some seconds and sends another request.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:45.0) Gecko/20100101 Firefox/45.0'
    }
    request_succeed = False
    while not request_succeed:
        try:
            response = requests.get(url, timeout=5, headers=headers)
            request_succeed = True
        except requests.exceptions.ReadTimeout:
            logging.error(f'ReadTimeout, user URL: {url}')
            time.sleep(1)
        except requests.exceptions.ConnectionError:
            logging.error(f'ConnectionError, user URL: {url}')
            time.sleep(1)
    response.encoding = 'utf8'
    return response.text


def parse_url(url):
    """Parses provided URL. Define whether the URL contains 32-digits UNIQUE_ID. If true, returns this id.

    If the URL contains only the word "posts", returns None. If URL is incorrect, returns 404
    """
    latest_slash = url[len(url) - 1]
    if latest_slash == '/' and url[:5] == 'posts':
        id_start_index = 6
        if len(url) > id_start_index:
            id = url[id_start_index:len(url) - 1]
            if len(id) == 32:
                return id
            return 404
        return
    return 404
