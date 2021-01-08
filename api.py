from reddit_parser import PostsProcessor
from utils import check_duplicates, define_path_to_file, find_line_index, make_dict_from_str, make_str_from_dict
import json
import os


def get_posts():
    """Tries to convert each string from reddit-file to dictionary and add this dictionary to list.

    Returns generated list in JSON format and status code 200 if reddit-file exists and isn't empty.
    In all other cases, status code 404 is only returned.
    """
    REDDIT_FILENAME_PREFIX = 'reddit-'
    file_path = define_path_to_file(REDDIT_FILENAME_PREFIX, os.path.dirname(__file__))
    NOT_FOUND = 404
    if not file_path:
        return {'status_code': NOT_FOUND}
    posts = []
    with open(file_path) as file:
        for line in file:
            post_dict = make_dict_from_str(line)
            posts.append(post_dict)
    if not posts:
        return {'status_code': NOT_FOUND}
    OK = 200
    return {'status_code': OK, 'content': json.dumps(posts)}


def get_line(unique_id):
    """Tries to find a string with specified UNIQUE_ID in reddit-file.

    If reddit-file exists and the search was successful, converts found string to dictionary
    and returns this dictionary in JSON format with status code 200.
    In all other cases, status code 404 is only returned.
    """
    REDDIT_FILENAME_PREFIX = 'reddit-'
    file_path = define_path_to_file(REDDIT_FILENAME_PREFIX, os.path.dirname(__file__))
    NOT_FOUND = 404
    if not file_path:
        return {'status_code': NOT_FOUND}
    post_dict = {}
    with open(file_path) as file:
        for line in file:
            if unique_id in line:
                post_dict = make_dict_from_str(line)
                break
    if not post_dict:
        return {'status_code': NOT_FOUND}
    OK = 200
    return {'status_code': OK, 'content': json.dumps(post_dict)}


def add_line(post_dict):
    """Takes post data in JSON format, converts it to string and tries to add to reddit-file.

    If file doesn't exist the new one is generated. Returns JSON in the format {"UNIQUE_ID": inserted line number}
    and status code 201 if successful. If equal post data already exists in reddit-file, only returns status code 409.
    In all other cases, including incorrect post data, status code 404 is only returned.
    """
    REDDIT_FILENAME_PREFIX = 'reddit-'
    file_path = define_path_to_file(REDDIT_FILENAME_PREFIX, os.path.dirname(__file__))
    if not file_path:
        NEEDED_POSTS_COUNT = 100
        URL = "https://www.reddit.com/top/?t=month"
        PostsProcessor(URL, NEEDED_POSTS_COUNT)
    post_dict = json.loads(post_dict)
    CORRECT_POST_ENTITIES_COUNT = 11
    if not len(post_dict) == CORRECT_POST_ENTITIES_COUNT:
        NOT_FOUND = 404
        return {'status_code': NOT_FOUND}
    post_data_str = make_str_from_dict(post_dict)
    posts_list = open(file_path).readlines()
    if not check_duplicates(post_data_str, posts_list):
        CONFLICT = 409
        return {'status_code': CONFLICT}
    if posts_list:
        posts_list[len(posts_list) - 1] += '\n'
    posts_list.append(post_data_str)
    with open(file_path, 'w') as file:
        file.writelines(posts_list)
    CREATED = 201
    inserted_line_number = len(posts_list)
    content = json.dumps({'UNIQUE_ID': inserted_line_number})
    return {'status_code': CREATED, 'content': content}


def del_line(unique_id):
    """Tries to find a string with specified UNIQUE_ID in reddit-file. If reddit-file exists

    and the search was successful, deletes found string from the file and returns status code 200.
    In all other cases, status code 404 is returned.
    """
    REDDIT_FILENAME_PREFIX = 'reddit-'
    file_path = define_path_to_file(REDDIT_FILENAME_PREFIX, os.path.dirname(__file__))
    NOT_FOUND = 404
    if not file_path:
        return {'status_code': NOT_FOUND}
    posts_list = open(file_path).readlines()
    line_index = find_line_index(unique_id, posts_list)
    if line_index:
        del posts_list[line_index]
        posts_list[len(posts_list) - 1] = posts_list[len(posts_list) - 1].replace('\n', '')
        with open(file_path, 'w') as file:
            file.writelines(posts_list)
        OK = 200
        return {'status_code': OK}
    return {'status_code': NOT_FOUND}


def change_line(unique_id, post_dict):
    """Takes post data in JSON format, converts it to string and tries to modify the content

    of a line with specified UNIQUE_ID in reddit-file. Returns status code 200 if successful.
    If equal post data already exists in the file, returns status code 409.
    In all other cases, status code 404 is returned.
    """
    REDDIT_FILENAME_PREFIX = 'reddit-'
    file_path = define_path_to_file(REDDIT_FILENAME_PREFIX, os.path.dirname(__file__))
    NOT_FOUND = 404
    if not file_path:
        return {'status_code': NOT_FOUND}
    post_dict = json.loads(post_dict)
    CORRECT_POST_ENTITIES_COUNT = 11
    if len(post_dict) != CORRECT_POST_ENTITIES_COUNT:
        return {'status_code': NOT_FOUND}
    posts_list = open(file_path).readlines()
    line_index = find_line_index(unique_id, posts_list)
    if not line_index:
        return {'status_code': NOT_FOUND}
    post_data_str = make_str_from_dict(post_dict)
    stored_str = posts_list[line_index].replace('\n', '')
    if post_data_str == stored_str:
        CONFLICT = 409
        return {'status_code': CONFLICT}
    if line_index != len(posts_list):
        post_data_str += '\n'
    posts_list[line_index] = post_data_str
    with open(file_path, 'w') as file:
        file.writelines(posts_list)
    OK = 200
    return {'status_code': OK}
