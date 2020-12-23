from reddit_parser import PostsProcessor
from postgre import PostgreAllPostsGetter, PostgreExecuterError, PostgrePostGetter, PostgrePostInserter, \
    PostgrePostRemover, PostgrePostUpdater
from utils import DataConverter
import json
import logging


def get_posts():
    with PostgreAllPostsGetter() as posts_getter:
        stored_posts = []
        try:
            stored_posts = posts_getter.get_all_posts_from_db()
        except PostgreExecuterError as err:
            logging.error(f'{err.thrown_by}: {err.text}')
    if stored_posts:
        posts = [DataConverter.make_dict_from_tuple(tup) for tup in stored_posts]
        return {'status_code': 200, 'content': json.dumps(posts)}
    return {'status_code': 404}


def get_line(unique_id):
    with PostgrePostGetter(unique_id) as post_getter:
        stored_post = ()
        try:
            stored_post = post_getter.get_post_from_db()
        except PostgreExecuterError as err:
            logging.error(f'{err.thrown_by}: {err.text}')
    if stored_post:
        post = DataConverter.make_dict_from_tuple(stored_post)
        return {'status_code': 200, 'content': json.dumps(post)}
    return {'status_code': 404}


def add_line(post_dict):
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
    content = json.dumps({'UNIQUE_ID': stored_post_number + 1})
    return {'status_code': status_code, 'content': content}


def del_line(unique_id):
    status_code = 404
    with PostgrePostRemover(unique_id) as post_remover:
        deleted_post_number = 0
        try:
            deleted_post_number = post_remover.remove_post_from_db()
        except PostgreExecuterError as err:
            logging.error(f'{err.thrown_by}: {err.text}')
    if deleted_post_number:
        status_code = 200
    return {'status_code': status_code}


def change_line(unique_id, post_dict):
    post_dict = json.loads(post_dict)
    post_dict_unique_id = post_dict.get('unique_id')
    provided_id_match = True
    if post_dict_unique_id:
        provided_id_match = post_dict_unique_id == unique_id
    else:
        post_dict['unique_id'] = unique_id
    status_code = 404
    if len(post_dict) == 11 and unique_id and len(unique_id) == 32 and provided_id_match:
        post_dict_with_zero = DataConverter.convert_date(post_dict.copy(), 'day')
        post_dict = DataConverter.convert_date(post_dict, 'month')
        with PostgrePostUpdater(unique_id, post_dict) as post_updater:
            stored_post = ()
            try:
                stored_post = post_updater.get_post_from_db()
            except PostgreExecuterError as err:
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
    status_code, stored_post_number = 404, None
    with PostgrePostInserter(unique_id, post_dict) as post_inserter:
        try:
            stored_post = post_inserter.get_post_from_db()
        except PostgreExecuterError as err:
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
    return status_code, stored_post_number
