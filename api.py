from reddit_parser import PostsProcessor
from postgre import PostgreAllPostsGetter, PostgreExecutorError, PostgrePostGetter, PostgrePostInserter, \
    PostgrePostRemover, PostgrePostUpdater
from utils import DataConverter
import json
import logging


def get_posts():
    """Tries to get all posts from a database, converts each post data to a dictionary

    and add this dictionary to list. If Executor error was thrown, logs it.
    If generated list isn't empty, returns it in JSON format
    with status code 200. In all other cases, status code 404 is only returned.
    """
    with PostgreAllPostsGetter() as posts_getter:
        stored_posts = []
        try:
            stored_posts = posts_getter.get_all_posts_from_db()
        except PostgreExecutorError as err:
            logging.error(f'{err.thrown_by}: {err.text}')
    if stored_posts:
        posts = [DataConverter.make_dict_from_tuple(tup) for tup in stored_posts]
        return {'status_code': 200, 'content': json.dumps(posts)}
    return {'status_code': 404}


def get_post(unique_id):
    """Tries to get a post from a database by its unique id, converts obtained post data to a dictionary.

    If Executor error was thrown, logs it. If post was found, returns generated dictionary in JSON format
    with status code 200. In all other cases, status code 404 is only returned.
    """
    with PostgrePostGetter(unique_id) as post_getter:
        stored_post = ()
        try:
            stored_post = post_getter.get_post_from_db()
        except PostgreExecutorError as err:
            logging.error(f'{err.thrown_by}: {err.text}')
    if stored_post:
        post = DataConverter.make_dict_from_tuple(stored_post)
        return {'status_code': 200, 'content': json.dumps(post)}
    return {'status_code': 404}


def add_post(post_dict):
    """Takes post data in JSON format, verifies this data and tries to insert it to the tables.

    Returns JSON in the format {"UNIQUE_ID": inserted post number} with status code 201 if successful.
    Status code can take the value 409 or 404, in such cases the function returns only defined code.
    Status code is 409, if equal post data already exists in a database or it's 404 in another unsuccessful instances.
    """
    post_dict = json.loads(post_dict)
    unique_id = post_dict.get('unique_id')
    status_code = 404
    stored_post_number = 0
    if len(post_dict) == 11 and unique_id and len(unique_id) == 32:
        post_dict = DataConverter.convert_date(post_dict, 'month')
        status_code, stored_post_number = insert_post(unique_id, post_dict)
        if not status_code:
            status_code, stored_post_number = insert_post(unique_id, post_dict)
    if not status_code == 201:
        return {'status_code': status_code}
    content = json.dumps({'UNIQUE_ID': stored_post_number})
    return {'status_code': status_code, 'content': content}


def del_post(unique_id):
    """Tries to delete a post from a database by its unique id.

    If the post was found and successfully deleted, returns status code 200.
    In all other cases, status code 404 is returned.
    Logs Executor error, if it was thrown.
    """
    status_code = 404
    with PostgrePostRemover(unique_id) as post_remover:
        deleted_post_number = 0
        try:
            deleted_post_number = post_remover.remove_post_from_db()
        except PostgreExecutorError as err:
            logging.error(f'{err.thrown_by}: {err.text}')
    if deleted_post_number:
        status_code = 200
    return {'status_code': status_code}


def update_post(unique_id, post_dict):
    """Takes unique id of the post and and its new data in JSON format.

    Verifies these data, tries to find such post in a database by its unique id.
    If the post was found and its data isn't equivalent to the data at which it should be replaced,
    modifies post data records in the related tables and returns status code 200.
    If equal post data already exists in a database, returns status code 409.
    In all other cases, status code 404 is returned.
    Logs Executor error, if it was thrown.
    """
    post_dict = json.loads(post_dict)
    post_dict_unique_id = post_dict.get('unique_id')
    provided_id_match = True
    if post_dict_unique_id:
        provided_id_match = post_dict_unique_id == unique_id
    else:
        post_dict['unique_id'] = unique_id
    status_code = 404
    if len(post_dict) == 11 and unique_id and len(unique_id) == 32 and provided_id_match:
        post_dict_with_zero = DataConverter.convert_date(post_dict.copy(), 'zero')
        post_dict = DataConverter.convert_date(post_dict, 'month')
        with PostgrePostUpdater(unique_id, post_dict) as post_updater:
            stored_post = ()
            try:
                stored_post = post_updater.get_post_from_db()
            except PostgreExecutorError as err:
                logging.error(f'{err.thrown_by}: {err.text}')
            if stored_post:
                stored_post_dict = DataConverter.make_dict_from_tuple(stored_post)
                if post_dict_with_zero == stored_post_dict:
                    status_code = 409
                else:
                    post_updater.update_post()
                    status_code = 200
    return {'status_code': status_code}


def insert_post(unique_id, post_dict):
    """Takes unique id of the post and its data in JSON format.

    Tries to find a post in related tables.
    If there are no such tables, logs Executor error, parses data from reddit.com,
    stores found post data in the database and shuts down.
    If the post was found, returns status code 409.
    If the post with indicated unique id doesn't exist in the table, saves provided post data to it,
    on condition that current number of database records does not exceed 1000.
    In the present case, status code 201 and the number of stored posts are returned.
    """
    status_code, stored_post_number = 404, 0
    with PostgrePostInserter(unique_id, post_dict) as post_inserter:
        try:
            stored_post = post_inserter.get_post_from_db()
        except PostgreExecutorError as err:
            logging.error(f'{err.thrown_by}: {err.text}')
            PostsProcessor("https://www.reddit.com/top/?t=month", 100)
            return None, None
        if stored_post:
            status_code = 409
        else:
            stored_post_number = post_inserter.define_stored_post_number()
            if stored_post_number < 1000:
                post_inserter.insert_post_into_db()
                status_code = 201
    return status_code, stored_post_number + 1
