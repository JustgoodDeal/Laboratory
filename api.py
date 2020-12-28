from mongo import MongoExecutor
from reddit_parser import PostsProcessor
import json


def get_posts():
    """Tries to get all posts from a database. If any post was found, returns status code 200

    and a list with found posts in JSON format. In all other cases, status code 404 is only returned.
    """
    stored_posts = MongoExecutor().get_all_posts_from_db()
    if stored_posts:
        return {'status_code': 200, 'content': json.dumps(stored_posts)}
    return {'status_code': 404}


def get_post(unique_id):
    """Tries to get a post from a database by its unique id.

    If post was found, returns status code 200 and a dictionary with post data in JSON format.
    In all other cases, status code 404 is only returned """
    stored_post = MongoExecutor(unique_id=unique_id).get_post_from_db()
    if stored_post:
        return {'status_code': 200, 'content': json.dumps(stored_post)}
    return {'status_code': 404}


def add_post(post_dict):
    """Takes post data in JSON format, verifies this data and inserts it to the collections.

    Returns JSON in the format {"UNIQUE_ID": inserted post number} with status code 201 if successful.
    Status code can take the value 409 or 404, in such cases the function returns only defined code.
    Status code is 409, if equal post data already exists in a database.
    In all other cases, including current number of database records, exceeding 999, status code takes the value 404.
    """
    post_dict = json.loads(post_dict)
    post_unique_id = post_dict.get('post', {}).get('unique_id')
    user_unique_id = post_dict.get('user', {}).get('post_unique_id')
    stored_posts_number = 0
    status_code = 404
    if len(post_dict) == 2 and post_unique_id and len(post_unique_id) == 32 and post_unique_id == user_unique_id:
        mongo_executor = MongoExecutor(unique_id=post_unique_id)
        stored_posts_number = mongo_executor.define_stored_posts_number()
        if not stored_posts_number:
            PostsProcessor("https://www.reddit.com/top/?t=month", 100)
            stored_posts_number = mongo_executor.define_stored_posts_number()
        if mongo_executor.get_post_data_from_db():
            status_code = 409
        elif stored_posts_number < 1000:
            mongo_executor.insert_post_into_db(post_dict)
            status_code = 201
    if not status_code == 201:
        return {'status_code': status_code}
    content = json.dumps({'UNIQUE_ID': stored_posts_number + 1})
    return {'status_code': status_code, 'content': content}


def del_post(unique_id):
    """Tries to delete a post from a database by its unique id. If the post was found and successfully

    deleted, returns status code 200. In all other cases, status code 404 is returned.
    """
    status_code = 404
    deleted_documents_count = MongoExecutor(unique_id=unique_id).delete_post()
    if deleted_documents_count == 2:
        status_code = 200
    return {'status_code': status_code}


def update_post(unique_id, post_dict):
    """Takes unique id of the post and and its new data in JSON format.

    Verifies these data, tries to find such post in a database by its unique id.
    If the post was found and its data isn't equivalent to the data at which it should be replaced,
    modifies post data records in related collections and returns status code 200.
    If equal post data already exists in a database, returns status code 409.
    In all other cases, status code 404 is returned.
    """
    post_dict = json.loads(post_dict)
    post_dict.get('post', {})['unique_id'] = unique_id
    post_dict.get('user', {})['post_unique_id'] = unique_id
    status_code = 404
    if len(post_dict) == 2 and unique_id and len(unique_id) == 32:
        mongo_executor = MongoExecutor(unique_id=unique_id)
        stored_post_dict = mongo_executor.get_post_from_db()
        if stored_post_dict:
            if stored_post_dict == post_dict:
                status_code = 409
            else:
                mongo_executor.update_post(post_dict)
                status_code = 200
    return {'status_code': status_code}
