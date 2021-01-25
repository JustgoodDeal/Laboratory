from reddit_parser import PostsProcessor
from utils import check_duplicates, define_path_to_file, find_line_index, make_dict_from_str, make_str_from_dict
import json
import math
import os


def get_posts():
    """Tries to convert each string from reddit-file to dictionary and add this dictionary to list.

    Returns generated list in JSON format and status code 200 if reddit-file exists and isn't empty.
    In all other cases, status code 404 is only returned.
    """
    reddit_filename_prefix = 'reddit-'
    file_path = define_path_to_file(reddit_filename_prefix, os.path.dirname(__file__))
    not_found = 404
    if not file_path:
        return {'status_code': not_found}
    posts = []
    with open(file_path) as file:
        for line in file:
            post_dict = make_dict_from_str(line)
            posts.append(post_dict)
    if not posts:
        return {'status_code': not_found}
    ok = 200
    return {'status_code': ok, 'content': posts}


def get_line(unique_id):
    """Tries to find a string with specified UNIQUE_ID in reddit-file.

    If reddit-file exists and the search was successful, converts found string to dictionary
    and returns this dictionary in JSON format with status code 200.
    In all other cases, status code 404 is only returned.
    """
    reddit_filename_prefix = 'reddit-'
    file_path = define_path_to_file(reddit_filename_prefix, os.path.dirname(__file__))
    not_found = 404
    if not file_path:
        return {'status_code': not_found}
    post_dict = {}
    with open(file_path) as file:
        for line in file:
            if unique_id in line:
                post_dict = make_dict_from_str(line)
                break
    if not post_dict:
        return {'status_code': not_found}
    ok = 200
    return {'status_code': ok, 'content': post_dict}


def add_line(post_dict):
    """Takes post data in JSON format, converts it to string and tries to add to reddit-file.

    If file doesn't exist the new one is generated. Returns JSON in the format {"UNIQUE_ID": inserted line number}
    and status code 201 if successful. If equal post data already exists in reddit-file, only returns status code 409.
    In all other cases, including incorrect post data, status code 404 is only returned.
    """
    reddit_filename_prefix = 'reddit-'
    file_path = define_path_to_file(reddit_filename_prefix, os.path.dirname(__file__))
    if not file_path:
        needed_posts_count = 100
        url = "https://www.reddit.com/top/?t=month"
        PostsProcessor(url, needed_posts_count)
    post_dict = json.loads(post_dict)
    correct_post_entities_count = 11
    if not len(post_dict) == correct_post_entities_count:
        not_found = 404
        return {'status_code': not_found}
    post_data_str = make_str_from_dict(post_dict)
    posts_list = open(file_path).readlines()
    if not check_duplicates(post_data_str, posts_list):
        conflict = 409
        return {'status_code': conflict}
    if posts_list:
        posts_list[len(posts_list) - 1] += '\n'
    posts_list.append(post_data_str)
    with open(file_path, 'w') as file:
        file.writelines(posts_list)
    created = 201
    inserted_line_number = len(posts_list)
    content = json.dumps({'UNIQUE_ID': inserted_line_number})
    return {'status_code': created, 'content': content}


def del_line(unique_id):
    """Tries to find a string with specified UNIQUE_ID in reddit-file. If reddit-file exists

    and the search was successful, deletes found string from the file and returns status code 200.
    In all other cases, status code 404 is returned.
    """
    reddit_filename_prefix = 'reddit-'
    file_path = define_path_to_file(reddit_filename_prefix, os.path.dirname(__file__))
    not_found = 404
    if not file_path:
        return {'status_code': not_found}
    posts_list = open(file_path).readlines()
    line_index = find_line_index(unique_id, posts_list)
    if line_index:
        del posts_list[line_index]
        posts_list[len(posts_list) - 1] = posts_list[len(posts_list) - 1].replace('\n', '')
        with open(file_path, 'w') as file:
            file.writelines(posts_list)
        ok = 200
        return {'status_code': ok}
    return {'status_code': not_found}


def change_line(unique_id, post_dict):
    """Takes post data in JSON format, converts it to string and tries to modify the content

    of a line with specified UNIQUE_ID in reddit-file. Returns status code 200 if successful.
    If equal post data already exists in the file, returns status code 409.
    In all other cases, status code 404 is returned.
    """
    reddit_filename_prefix = 'reddit-'
    file_path = define_path_to_file(reddit_filename_prefix, os.path.dirname(__file__))
    not_found = 404
    if not file_path:
        return {'status_code': not_found}
    post_dict = json.loads(post_dict)
    correct_post_entities_count = 11
    if len(post_dict) != correct_post_entities_count:
        return {'status_code': not_found}
    posts_list = open(file_path).readlines()
    line_index = find_line_index(unique_id, posts_list)
    if not line_index:
        return {'status_code': not_found}
    post_data_str = make_str_from_dict(post_dict)
    stored_str = posts_list[line_index].replace('\n', '')
    if post_data_str == stored_str:
        conflict = 409
        return {'status_code': conflict}
    if line_index != len(posts_list):
        post_data_str += '\n'
    posts_list[line_index] = post_data_str
    with open(file_path, 'w') as file:
        file.writelines(posts_list)
    ok = 200
    return {'status_code': ok}


def make_dict_from_get_params(get_params):
    """Parses URL's get parameters into a dictionary"""
    params_list = get_params.split('&')
    params_dict = {}
    for param in params_list:
        equal_sign_index = param.find('=')
        param_name = param[:equal_sign_index]
        param_value = param[equal_sign_index + 1:]
        params_dict[param_name] = param_value
    return params_dict


def filter_content(posts_list, get_params):
    """Filters posts list based on URL's get parameters. Returns only the part of posts,

    which should be displayed on specified page under pagination.
    """
    params_dict = make_dict_from_get_params(get_params)
    filter_by  = ('post_category', 'post_date', 'votes_number')
    post_category, post_date, votes_number = filter_by
    post_category_filter = params_dict.get(post_category, '')
    post_date_filter = params_dict.get(post_date, '')
    votes_number_filter = params_dict.get(votes_number, '')
    if any([post_category_filter, post_date_filter, votes_number_filter]):
        posts_list = [post for post in posts_list if post_category_filter in post[post_category] and
                      post_date_filter in post[post_date] and votes_number_filter in post[votes_number]]
    posts_count = len(posts_list)
    per_page = int(params_dict['per_page'])
    min_pages_count = 1
    pages = math.ceil(posts_count / per_page) or min_pages_count
    page = int(params_dict['page'])
    if page > pages:
        default_page = 1
        page = default_page
    posts_start_index = (page - 1) * per_page
    posts_end_index = page * per_page
    posts_list = posts_list[posts_start_index:posts_end_index]
    content = {'pages': pages, 'page': page, 'posts': posts_list}
    return content
