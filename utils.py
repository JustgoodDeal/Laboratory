import datetime
import logging
import os
import requests
import time
import yaml


class DataConverter:
    @staticmethod
    def make_str_from_dict(post_dict):
        """Converts dictionary with post data to string"""
        post_data_str = ''
        for data_name in post_dict:
            data_value = post_dict[data_name]
            post_data_str += f'{data_value};'
        return post_data_str[:len(post_data_str) - 1]

    @staticmethod
    def make_dict_from_str(data_str):
        """Converts string with post data to dictionary in a specific sequence"""
        dict_order = ['UNIQUE_ID', 'post URL', 'username', 'user karma', 'user cake day', 'post karma', 'comment karma',
                      'post date', 'number of comments', 'number of votes', 'post category']
        post_data = data_str.replace('\n', '').split(';')
        post_dict = {}
        for ind in range(len(dict_order)):
            post_dict[dict_order[ind]] = post_data[ind]
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
        return date.strftime("%d.%m.%Y")

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


def define_path_to_file(prefix):
    """Defines path to the file existing in the directory under the prefix contained in the file name"""
    work_dir_path = os.getcwd()
    for name in os.listdir(work_dir_path):
        if os.path.isfile(name) and prefix in name:
            return os.path.join(work_dir_path, name)


def check_duplicates(post_data_str, posts_list):
    """Takes post data string and defines part of it being post unique id. If any of the strings from taken list

    contains the same unique id, returns None (duplicate found); otherwise, returns True (no duplicates).
    """
    sent_id = post_data_str[:32]
    for post_str in posts_list:
        stored_id = post_str[:32]
        if sent_id == stored_id:
            return
    return True


def find_line_index(sent_id, posts_list):
    """Takes post unique id. If is detected that one of the strings from taken

    list contains the same unique id, returns line index of this string.
    """
    for ind, post_str in enumerate(posts_list):
        stored_id = post_str[:32]
        if sent_id == stored_id:
            return ind
    return


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
