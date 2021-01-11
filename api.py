import mongo
import reddit_parser
import json


def get_posts():
    """Tries to get all posts from a database. If any post was found, returns status code 200

    and a list with found posts in JSON format. In all other cases, status code 404 is only returned.
    """
    stored_posts = mongo.MongoExecutor().get_all_posts_from_db()
    if stored_posts:
        OK = 200
        return {'status_code': OK, 'content': json.dumps(stored_posts)}
    NOT_FOUND = 404
    return {'status_code': NOT_FOUND}


def get_post(unique_id):
    """Tries to get a post from a database by its unique id.

    If post was found, returns status code 200 and a dictionary with post data in JSON format.
    In all other cases, status code 404 is only returned """
    stored_post = mongo.MongoExecutor(unique_id=unique_id).get_post_from_db()
    if stored_post:
        OK = 200
        return {'status_code': OK, 'content': json.dumps(stored_post)}
    NOT_FOUND = 404
    return {'status_code': NOT_FOUND}


def add_post(post_dict):
    """Takes post data in JSON format, verifies this data and inserts it to the collections.

    Returns JSON in the format {"UNIQUE_ID": inserted post number} with status code 201 if successful.
    Status code can take the value 409 or 404, in such cases the function returns only defined code.
    Status code is 409, if equal post data already exists in a database.
    In all other cases, including current number of database records, exceeding 999, status code takes the value 404.
    """
    post_dict = json.loads(post_dict)
    POST_ENTITIES_KEY = 'post'
    POST_DOC_UNIQUE_ID_KEY = 'unique_id'
    post_unique_id = post_dict.get(POST_ENTITIES_KEY, {}).get(POST_DOC_UNIQUE_ID_KEY, '')
    USER_ENTITIES_KEY = 'user'
    USER_DOC_RELATED_POST_UNIQUE_ID_KEY = 'post_unique_id'
    user_unique_id = post_dict.get(USER_ENTITIES_KEY, {}).get(USER_DOC_RELATED_POST_UNIQUE_ID_KEY, '')
    NOT_FOUND = 404
    CORRECT_DOC_COUNT = 2
    CORRECT_ID_LEN = 32
    if len(post_dict) != CORRECT_DOC_COUNT or len(post_unique_id) != CORRECT_ID_LEN or post_unique_id != user_unique_id:
        return {'status_code': NOT_FOUND}
    mongo_executor = mongo.MongoExecutor(unique_id=post_unique_id)
    stored_posts_number = mongo_executor.define_stored_posts_number()
    if not stored_posts_number:
        NEEDED_POSTS_NUMBER = 100
        REDDIT_URL = "https://www.reddit.com/top/?t=month"
        reddit_parser.PostsProcessor(REDDIT_URL, NEEDED_POSTS_NUMBER)
        stored_posts_number = mongo_executor.define_stored_posts_number()
    if mongo_executor.get_post_data_from_db():
        CONFLICT = 409
        return {'status_code': CONFLICT}
    MAX_STORED_POSTS_NUMBER = 1000
    if stored_posts_number < MAX_STORED_POSTS_NUMBER:
        mongo_executor.insert_post_into_db(post_dict)
        CREATED = 201
        content = json.dumps({'UNIQUE_ID': stored_posts_number + 1})
        return {'status_code': CREATED, 'content': content}
    return {'status_code': NOT_FOUND}


def del_post(unique_id):
    """Tries to delete a post from a database by its unique id. If the post was found and successfully

    deleted, returns status code 200. In all other cases, status code 404 is returned.
    """
    deleted_documents_count = mongo.MongoExecutor(unique_id=unique_id).delete_post()
    NEEDED_NUMBER_FOR_REMOVAL = 2
    if deleted_documents_count == NEEDED_NUMBER_FOR_REMOVAL:
        OK = 200
        return {'status_code': OK}
    NOT_FOUND = 404
    return {'status_code': NOT_FOUND}


def update_post(unique_id, post_dict):
    """Takes unique id of the post and and its new data in JSON format.

    Verifies these data, tries to find such post in a database by its unique id.
    If the post was found and its data isn't equivalent to the data at which it should be replaced,
    modifies post data records in related collections and returns status code 200.
    If equal post data already exists in a database, returns status code 409.
    In all other cases, status code 404 is returned.
    """
    post_dict = json.loads(post_dict)
    POST_ENTITIES_KEY = 'post'
    POST_DOC_UNIQUE_ID_KEY = 'unique_id'
    post_dict.get(POST_ENTITIES_KEY, {})[POST_DOC_UNIQUE_ID_KEY] = unique_id
    USER_ENTITIES_KEY = 'user'
    USER_DOC_RELATED_POST_UNIQUE_ID_KEY = 'post_unique_id'
    post_dict.get(USER_ENTITIES_KEY, {})[USER_DOC_RELATED_POST_UNIQUE_ID_KEY] = unique_id
    CORRECT_DOC_COUNT = 2
    CORRECT_ID_LEN = 32
    NOT_FOUND = 404
    if len(post_dict) != CORRECT_DOC_COUNT or not unique_id or len(unique_id) != CORRECT_ID_LEN:
        return {'status_code': NOT_FOUND}
    mongo_executor = mongo.MongoExecutor(unique_id=unique_id)
    stored_post_dict = mongo_executor.get_post_from_db()
    if not stored_post_dict:
        return {'status_code': NOT_FOUND}
    if stored_post_dict == post_dict:
        CONFLICT = 409
        return {'status_code': CONFLICT}
    mongo_executor.update_post(post_dict)
    OK = 200
    return {'status_code': OK}
