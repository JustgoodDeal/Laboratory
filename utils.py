from shutil import copy2
import datetime
import logging
import os
import requests
import time
import yaml


def check_duplicates(post_data_str, posts_list):
    """Takes post data string and defines part of it being post unique id. If any of the strings from taken list

    contains the same unique id, returns False (duplicate found); otherwise, returns True (no duplicates).
    """
    UNIQUE_ID_LENGTH = 32
    sent_id = post_data_str[:UNIQUE_ID_LENGTH]
    for post_str in posts_list:
        stored_id = post_str[:UNIQUE_ID_LENGTH]
        if sent_id == stored_id:
            return False
    return True


def convert_data_from_yaml_to_dict(path_to_config_file):
    """Tries to convert data from config file in yaml format to dictionary. If the config file contains

    data which couldn't be converted to dictionary or yaml file doesn't exist, returns empty dictionary.
    """
    config_dict = {}
    try:
        with open(path_to_config_file) as file:
            config_dict = yaml.safe_load(file)
            if not type(config_dict) is dict:
                config_dict = {}
    except FileNotFoundError:
        pass
    return config_dict


def convert_time_lapse_to_date(date_str):
    """Takes a string containing time lapse between publishing post and current time.

    ('just now', '7 days ago', '1 month ago', etc.). Converts it to the date when the post was published.
    """
    POSTED_NOW = 'just now'
    POSTED_SOME_HOURS_AGO = 'hour'
    POSTED_MONTH_AGO = 'month'
    if POSTED_NOW in date_str or POSTED_SOME_HOURS_AGO in date_str:
        TODAY = 0
        days = TODAY
    elif POSTED_MONTH_AGO in date_str:
        DAYS_IN_MONTH = 31
        days = DAYS_IN_MONTH
    else:
        DAYS_COUNT_INDEX = 0
        days = int(date_str.split()[DAYS_COUNT_INDEX])
    date = datetime.datetime.today() - datetime.timedelta(days=days)
    return date.strftime("%d.%m.%Y")


def define_filename(file_format):
    """Defines the name of output file based on the file format and current time"""
    datetime_now = datetime.datetime.now()
    datetime_str = datetime_now.strftime("%Y%m%d%H%M")
    REDDIT_FILENAME_PREFIX = 'reddit-'
    file_name = f'{REDDIT_FILENAME_PREFIX}{datetime_str}.{file_format}'
    return file_name


def define_path_to_webdriver():
    """Defines path to Chrome webdriver under config file"""
    CONFIG_FILENAME = 'config.yaml'
    path_to_config_file = os.path.join(os.path.dirname(__file__), CONFIG_FILENAME)
    config_dict = convert_data_from_yaml_to_dict(path_to_config_file)
    PATH_KEY = 'executable_path'
    path_from_config = config_dict.get(PATH_KEY)
    DEFAULT_PATH = 'chromedriver'
    executable_path = path_from_config if path_from_config else DEFAULT_PATH
    return executable_path


def define_path_to_file(filename_prefix, path_to_directory):
    """Defines path to the file existing in the directory under the prefix contained in the file name"""
    for name in os.listdir(path_to_directory):
        path_to_file = os.path.join(path_to_directory, name)
        if os.path.isfile(path_to_file) and filename_prefix in name:
            return path_to_file
    return False


def find_line_index(sent_id, posts_list):
    """Takes post unique id. If is detected that one of the strings from taken

    list contains the same unique id, returns line index of this string.
    """
    UNIQUE_ID_LENGTH = 32
    for ind, post_str in enumerate(posts_list):
        stored_id = post_str[:UNIQUE_ID_LENGTH]
        if sent_id == stored_id:
            return ind
    return False


def get_html(url):
    """Sends a request to indicated URL and return server response text in HTML format.

    In case of ReadTimeout or Connection error, logs it, suspends execution of a program
    for some seconds and sends another request.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:45.0) Gecko/20100101 Firefox/45.0'
    }
    request_succeed = False
    WAIT_RESPONSE_SECONDS = 5
    WAIT_NEXT_TRY_SECONDS = 1
    while not request_succeed:
        try:
            response = requests.get(url, timeout=WAIT_RESPONSE_SECONDS, headers=headers)
            request_succeed = True
        except requests.exceptions.ReadTimeout:
            ERROR_TEXT = 'ReadTimeout'
            logging.error(f'{ERROR_TEXT}, user URL: {url}')
            time.sleep(WAIT_NEXT_TRY_SECONDS)
        except requests.exceptions.ConnectionError:
            ERROR_TEXT = 'ConnectionError'
            logging.error(f'{ERROR_TEXT}, user URL: {url}')
            time.sleep(WAIT_NEXT_TRY_SECONDS)
    response.encoding = 'utf8'
    return response.text


def make_dict_from_str(data_str):
    """Converts string with post data to dictionary in a specific sequence"""
    dict_order = ['UNIQUE_ID', 'post URL', 'username', 'user karma', 'user cake day', 'post karma', 'comment karma',
                  'post date', 'number of comments', 'number of votes', 'post category']
    line_data_list = data_str.replace('\n', '').split(';')
    post_dict = {}
    for ind in range(len(dict_order)):
        post_dict[dict_order[ind]] = line_data_list[ind]
    return post_dict


def make_str_from_dict(post_dict):
    """Converts dictionary with post data to string"""
    post_data_str = ''
    for data_name in post_dict:
        data_value = post_dict[data_name]
        post_data_str += f'{data_value};'
    return post_data_str[:len(post_data_str) - 1]


def parse_url(url):
    """Parses provided URL. Define whether the URL contains 32-digits UNIQUE_ID. If true, returns this id.

    If the URL contains only the word "posts", returns False. If URL is incorrect, returns 404
    """
    latest_slash = url[len(url) - 1]
    URL_IS_INCORRECT = 404
    URL_WITHOUT_ID = False
    POSTS_LENGTH = 5
    if latest_slash != '/' or url[:POSTS_LENGTH] != 'posts':
        return URL_IS_INCORRECT
    UNIQUE_ID_START_INDEX = 6
    if len(url) <= UNIQUE_ID_START_INDEX:
        return URL_WITHOUT_ID
    unique_id = url[UNIQUE_ID_START_INDEX:len(url) - 1]
    UNIQUE_ID_LENGTH = 32
    if len(unique_id) == UNIQUE_ID_LENGTH:
        return unique_id
    return URL_IS_INCORRECT


def posts_list_is_ready_check(posts_list, needed_posts_count, stop_count):
    """Checks whether order and count of the posts meeting the criteria corresponds to needed"""
    if len(posts_list) == stop_count or not stop_count:
        return True
    if len(posts_list) < needed_posts_count or not posts_list:
        return False
    posts_list_copy = posts_list.copy()
    POST_ORDER_INDEX_KEY = 'post_index'
    posts_list_copy = sorted(posts_list_copy, key=lambda post_dict: post_dict[POST_ORDER_INDEX_KEY])
    init_list_slice = posts_list_copy[:needed_posts_count]
    right_posts_order = init_list_slice[len(init_list_slice) - 1][POST_ORDER_INDEX_KEY] == needed_posts_count - 1
    if not right_posts_order:
        return False
    UNSUITABLE_DICT_LEN = 1
    unsuitable_posts_count = len([post_dict for post_dict in init_list_slice if len(post_dict) == UNSUITABLE_DICT_LEN])
    if needed_posts_count + unsuitable_posts_count == len(init_list_slice):
        return True
    for post_dict_index in range(needed_posts_count, len(posts_list_copy)):
        current_post_dict = posts_list_copy[post_dict_index]
        right_posts_order = current_post_dict[POST_ORDER_INDEX_KEY] == post_dict_index
        if not right_posts_order:
            continue
        if len(current_post_dict) == UNSUITABLE_DICT_LEN:
            unsuitable_posts_count += 1
            continue
        further_list_slice = posts_list_copy[:post_dict_index + 1]
        if needed_posts_count + unsuitable_posts_count == len(further_list_slice):
            return True
    return False


def produce_data_file(post_data):
    """Writes stringified post data to output file after having removed previous one if existing"""
    remove_old_file()
    write_data_to_new_file(post_data)


def remove_old_file():
    """Removes no longer needed post data file if existing"""
    REDDIT_FILENAME_PREFIX = 'reddit-'
    path_to_old_file = define_path_to_file(REDDIT_FILENAME_PREFIX, os.path.dirname(__file__))
    if path_to_old_file:
        os.remove(path_to_old_file)


def replace_reddit_by_test_file(reddit_test_file_name):
    """Replaces reddit-file by test-file. Copies existing reddit-file to temporary while maintaining

    its original name, keeping it in the name of the temporary file.
    Removes reddit-file and copies test-file to the file with specified name.
    If initially reddit-file didn't exist the creation of temporary file is skipped.
    """
    path_to_directory = os.path.dirname(__file__)
    REDDIT_FILENAME_PREFIX = 'reddit-'
    path_to_reddit_file = define_path_to_file(REDDIT_FILENAME_PREFIX, path_to_directory)
    if path_to_reddit_file:
        chars_count_to_skip = len(REDDIT_FILENAME_PREFIX)
        reddit_f_datetime_start_ind = path_to_reddit_file.rfind(REDDIT_FILENAME_PREFIX) + chars_count_to_skip
        reddit_f_datetime = path_to_reddit_file[reddit_f_datetime_start_ind:]
        TEMP_FILENAME_PREFIX = 'temp-'
        path_to_temp_file = os.path.join(path_to_directory, f'{TEMP_FILENAME_PREFIX}{reddit_f_datetime}')
        copy2(path_to_reddit_file, path_to_temp_file)
        os.remove(path_to_reddit_file)
    TEST_FILENAME_PREFIX = 'test-'
    path_to_test_file = define_path_to_file(TEST_FILENAME_PREFIX, path_to_directory)
    copy2(path_to_test_file, os.path.join(path_to_directory, reddit_test_file_name))


def restore_pre_test_state(reddit_test_file_name):
    """Restores pre-test state of the directory. If tested file with specified name exists, removes it.

    If temporary file exists, defines original name of reddit-file, copies this file to the file
    with found name and removes temporary file.
    """
    path_to_directory = os.path.dirname(__file__)
    path_to_tested_file = os.path.join(path_to_directory, reddit_test_file_name)
    if os.path.exists(path_to_tested_file):
        os.remove(path_to_tested_file)
    TEMP_FILENAME_PREFIX = 'temp-'
    path_to_temp_file = define_path_to_file(TEMP_FILENAME_PREFIX, os.path.dirname(__file__))
    if path_to_temp_file:
        chars_count_to_skip = len(TEMP_FILENAME_PREFIX)
        former_reddit_file_datetime_start_index = path_to_temp_file.rfind(TEMP_FILENAME_PREFIX) + chars_count_to_skip
        former_reddit_file_datetime = path_to_temp_file[former_reddit_file_datetime_start_index:]
        REDDIT_FILENAME_PREFIX = 'reddit-'
        path_to_former_reddit_file = os.path.join(path_to_directory,
                                                  f'{REDDIT_FILENAME_PREFIX}{former_reddit_file_datetime}')
        copy2(path_to_temp_file, path_to_former_reddit_file)
        os.remove(path_to_temp_file)


def write_data_to_new_file(post_data):
    """Defines the path to output file and writes post data stringified from dictionary to that file"""
    FILE_FORMAT = 'txt'
    new_file_name = define_filename(FILE_FORMAT)
    path_to_new_file = os.path.join(os.path.dirname(__file__), new_file_name)
    with open(path_to_new_file, 'w') as file:
        for ind, post_dict in enumerate(post_data):
            post_data_str = make_str_from_dict(post_dict)
            if ind != len(post_data) - 1:
                post_data_str += '\n'
            file.write(post_data_str)
