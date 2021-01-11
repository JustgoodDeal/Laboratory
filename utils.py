import datetime
import logging
import mongo
import os
import requests
import tests
import time
import yaml


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


def convert_documents_into_post_dict(documents):
    """Takes a list of documents with post data from 2 tables, removes _id from each document

    and converts this documents to a post dictionary in a specific sequence."""
    post_dict = {}
    entity_order = ['post', 'user']
    for ind in range(len(entity_order)):
        entity_dict = documents[ind]
        DOCUMENT_ID = '_id'
        del entity_dict[DOCUMENT_ID]
        entity_name = entity_order[ind]
        post_dict[entity_name] = entity_dict
    return post_dict


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


def define_connection_entries(default_connection_entries):
    """Defines connection entries under config file. If any of the entry isn't specified

    in the config file, default value is set for this entry.
    """
    CONFIG_FILENAME = 'config.yaml'
    path_to_config_file = os.path.join(os.path.dirname(__file__), CONFIG_FILENAME)
    config_dict = convert_data_from_yaml_to_dict(path_to_config_file)
    conn_entries = {}
    for entry in default_connection_entries:
        conn_entries[entry] = config_dict.get(entry) or default_connection_entries[entry]
    return conn_entries


def define_database_name(default_database_name):
    """Defines database name under config file. If database name isn't specified

    in the config file, default value is set for this entry.
    """
    CONFIG_FILENAME = 'config.yaml'
    path_to_config_file = os.path.join(os.path.dirname(__file__), CONFIG_FILENAME)
    config_dict = convert_data_from_yaml_to_dict(path_to_config_file)
    DATABASE_KEY = 'database_name'
    database_name = config_dict[DATABASE_KEY] if config_dict.get(DATABASE_KEY) else default_database_name
    return database_name


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
    ENCODING = 'utf8'
    response.encoding = ENCODING
    return response.text


def posts_list_is_ready_check(posts_list, needed_posts_count, stop_count):
    """Checks whether order and count of the posts meeting the criteria corresponds to needed"""
    if len(posts_list) == stop_count or not stop_count:
        return True
    if len(posts_list) < needed_posts_count or not posts_list:
        return False
    posts_list_copy = posts_list.copy()
    POST_ENTITIES_KEY = 'post'
    POST_ORDER_INDEX_KEY = 'post_index'
    posts_list_copy = sorted(posts_list_copy, key=lambda post_dict: post_dict[POST_ENTITIES_KEY][POST_ORDER_INDEX_KEY])
    init_list_slice = posts_list_copy[:needed_posts_count]
    lates_element_index = init_list_slice[len(init_list_slice) - 1][POST_ENTITIES_KEY][POST_ORDER_INDEX_KEY]
    right_posts_order = lates_element_index == needed_posts_count - 1
    if not right_posts_order:
        return False
    UNSUITABLE_DICT_LEN = 1
    unsuitable_posts_count = len([post_dict for post_dict in init_list_slice
                                  if len(post_dict[POST_ENTITIES_KEY]) == UNSUITABLE_DICT_LEN])
    if needed_posts_count + unsuitable_posts_count == len(init_list_slice):
        return True
    for post_dict_index in range(needed_posts_count, len(posts_list_copy)):
        current_post_dict = posts_list_copy[post_dict_index]
        right_posts_order = current_post_dict[POST_ENTITIES_KEY][POST_ORDER_INDEX_KEY] == post_dict_index
        if not right_posts_order:
            continue
        if len(current_post_dict[POST_ENTITIES_KEY]) == UNSUITABLE_DICT_LEN:
            unsuitable_posts_count += 1
            continue
        further_list_slice = posts_list_copy[:post_dict_index + 1]
        if needed_posts_count + unsuitable_posts_count == len(further_list_slice):
            return True
    return False


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


def prepare_test_environment():
    """Creates a file indicating that unittests are have been running at the moment.

    Inserts certain test post data to the test collections.
    """
    path_to_test_mode_file = os.path.join(os.path.dirname(__file__), mongo.MongoExecutor.TEST_MODE_IDENTIFIER_FILENAME)
    with open(path_to_test_mode_file, 'w') as file:
        file.write('')
    mongo.MongoExecutor().insert_all_posts_into_db(tests.TestDataCollection.posts_list)


def restore_pre_test_state():
    """Restores pre-test state of the directory and database. Removes 2 test collections

    from a database, deletes a file indicating that unittests are have been running at the moment.
    """
    mongo.MongoExecutor().remove_collections()
    path_to_test_mode_file = os.path.join(os.path.dirname(__file__), mongo.MongoExecutor.TEST_MODE_IDENTIFIER_FILENAME)
    os.remove(path_to_test_mode_file)
