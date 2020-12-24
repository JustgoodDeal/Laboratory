from mongo import MongoExecuter
from reddit_parser import PostsProcessor
import json


def get_posts():
    stored_posts = MongoExecuter().get_all_posts_from_db()
    if stored_posts:
        return {'status_code': 200, 'content': json.dumps(stored_posts)}
    return {'status_code': 404}


def get_line(unique_id):
    stored_post = MongoExecuter(unique_id=unique_id).get_post_from_db()
    if stored_post:
        return {'status_code': 200, 'content': json.dumps(stored_post)}
    return {'status_code': 404}


def add_line(post_dict):
    post_dict = json.loads(post_dict)
    post_unique_id = post_dict.get('post', {}).get('unique_id')
    user_unique_id = post_dict.get('user', {}).get('post_unique_id')
    stored_posts_number = 0
    status_code = 404
    if len(post_dict) == 2 and post_unique_id and len(post_unique_id) == 32 and post_unique_id == user_unique_id:
        mongo_executer = MongoExecuter(post_dict=post_dict, unique_id=post_unique_id)
        stored_posts_number = mongo_executer.define_stored_posts_number()
        if not stored_posts_number:
            PostsProcessor("https://www.reddit.com/top/?t=month", 100)
            stored_posts_number = mongo_executer.define_stored_posts_number()
        if mongo_executer.get_post_data_from_db():
            status_code = 409
        elif stored_posts_number < 1000:
            mongo_executer.insert_post_into_db()
            status_code = 201
    if not status_code == 201:
        return {'status_code': status_code}
    content = json.dumps({'UNIQUE_ID': stored_posts_number + 1})
    return {'status_code': status_code, 'content': content}


def del_line(unique_id):
    status_code = 404
    deleted_documents_count = MongoExecuter(unique_id=unique_id).delete_post()
    if deleted_documents_count == 2:
        status_code = 200
    return {'status_code': status_code}


def change_line(unique_id, post_dict):
    post_dict = json.loads(post_dict)
    post_dict.get('post', {})['unique_id'] = unique_id
    post_dict.get('user', {})['post_unique_id'] = unique_id
    status_code = 404
    if len(post_dict) == 2 and unique_id and len(unique_id) == 32:
        mongo_executer = MongoExecuter(post_dict=post_dict, unique_id=unique_id)
        stored_post_dict = mongo_executer.get_post_from_db()
        if stored_post_dict:
            if stored_post_dict == post_dict:
                status_code = 409
            else:
                mongo_executer.update_post()
                status_code = 200
    return {'status_code': status_code}
