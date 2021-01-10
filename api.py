import postgre
import reddit_parser
import utils
import json
import logging


def get_posts():
    """Tries to get all posts from a database, converts each post data to a dictionary

    and add this dictionary to list. If Executor error was thrown, logs it.
    If generated list isn't empty, returns it in JSON format
    with status code 200. In all other cases, status code 404 is only returned.
    """
    with postgre.PostgreAllPostsGetter() as posts_getter:
        stored_posts = []
        try:
            stored_posts = posts_getter.get_all_posts_from_db()
        except postgre.PostgreExecutorError as err:
            logging.error(f'{err.thrown_by}: {err.text}')
    if not stored_posts:
        NOT_FOUND = 404
        return {'status_code': NOT_FOUND}
    posts = [utils.make_dict_from_tuple(tup) for tup in stored_posts]
    OK = 200
    return {'status_code': OK, 'content': json.dumps(posts)}


def get_post(unique_id):
    """Tries to get a post from a database by its unique id, converts obtained post data to a dictionary.

    If Executor error was thrown, logs it. If post was found, returns generated dictionary in JSON format
    with status code 200. In all other cases, status code 404 is only returned.
    """
    with postgre.PostgrePostGetter(unique_id) as post_getter:
        stored_post = ()
        try:
            stored_post = post_getter.get_post_from_db()
        except postgre.PostgreExecutorError as err:
            logging.error(f'{err.thrown_by}: {err.text}')
    if not stored_post:
        NOT_FOUND = 404
        return {'status_code': NOT_FOUND}
    post = utils.make_dict_from_tuple(stored_post)
    OK = 200
    return {'status_code': OK, 'content': json.dumps(post)}


def add_post(post_dict):
    """Takes post data in JSON format, verifies this data and tries to insert it to the tables.

    Returns JSON in the format {"UNIQUE_ID": inserted post number} with status code 201 if successful.
    Status code can take the value 409 or 404, in such cases the function returns only defined code.
    Status code is 409, if equal post data already exists in a database or it's 404 in another unsuccessful instances.
    """
    post_dict = json.loads(post_dict)
    UNIQUE_ID_KEY = 'unique_id'
    unique_id = post_dict.get(UNIQUE_ID_KEY)
    NOT_FOUND = 404
    CORRECT_POST_ENTITIES_COUNT = 11
    CORRECT_ID_LENGTH = 32
    if len(post_dict) != CORRECT_POST_ENTITIES_COUNT or not unique_id or len(unique_id) != CORRECT_ID_LENGTH:
        return {'status_code': NOT_FOUND}
    DATE_BEGINS_FROM_MONTH = 'month'
    post_dict = utils.convert_date(post_dict, DATE_BEGINS_FROM_MONTH)
    while True:
        status_code, stored_post_number = insert_post(unique_id, post_dict)
        if status_code:
            break
    if status_code == 201:
        content = json.dumps({'UNIQUE_ID': stored_post_number})
        return {'status_code': status_code, 'content': content}
    return {'status_code': status_code}


def del_post(unique_id):
    """Tries to delete a post from a database by its unique id.

    If the post was found and successfully deleted, returns status code 200.
    In all other cases, status code 404 is returned.
    Logs Executor error, if it was thrown.
    """
    with postgre.PostgrePostRemover(unique_id) as post_remover:
        deleted_post_number = 0
        try:
            deleted_post_number = post_remover.remove_post_from_db()
        except postgre.PostgreExecutorError as err:
            logging.error(f'{err.thrown_by}: {err.text}')
    if deleted_post_number:
        OK = 200
        return {'status_code': OK}
    NOT_FOUND = 404
    return {'status_code': NOT_FOUND}


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
    UNIQUE_ID_KEY = 'unique_id'
    post_dict_unique_id = post_dict.get(UNIQUE_ID_KEY)
    provided_id_match = True
    if post_dict_unique_id:
        provided_id_match = post_dict_unique_id == unique_id
    else:
        post_dict[UNIQUE_ID_KEY] = unique_id
    NOT_FOUND = 404
    CORRECT_POST_ENTITIES_COUNT = 11
    CORRECT_ID_LENGTH = 32
    if len(post_dict) != CORRECT_POST_ENTITIES_COUNT or not provided_id_match or len(unique_id) != CORRECT_ID_LENGTH:
        return {'status_code': NOT_FOUND}
    DATE_WITH_ZERO = 'zero'
    post_dict_with_renewed_date = utils.convert_date(post_dict.copy(), DATE_WITH_ZERO)
    DATE_BEGINS_FROM_MONTH = 'month'
    post_dict = utils.convert_date(post_dict, DATE_BEGINS_FROM_MONTH)
    with postgre.PostgrePostUpdater(unique_id, post_dict) as post_updater:
        stored_post = ()
        try:
            stored_post = post_updater.get_post_from_db()
        except postgre.PostgreExecutorError as err:
            logging.error(f'{err.thrown_by}: {err.text}')
        if not stored_post:
            return {'status_code': NOT_FOUND}
        stored_post_dict = utils.make_dict_from_tuple(stored_post)
        if post_dict_with_renewed_date == stored_post_dict:
            CONFLICT = 409
            return {'status_code': CONFLICT}
        post_updater.update_post()
        OK = 200
        return {'status_code': OK}


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
    with postgre.PostgrePostInserter(unique_id, post_dict) as post_inserter:
        try:
            stored_post = post_inserter.get_post_from_db()
        except postgre.PostgreExecutorError as err:
            logging.error(f'{err.thrown_by}: {err.text}')
            NEEDED_POSTS_NUMBER = 100
            REDDIT_URL = "https://www.reddit.com/top/?t=month"
            reddit_parser.PostsProcessor(REDDIT_URL, NEEDED_POSTS_NUMBER)
            return False, False
        if stored_post:
            CONFLICT = 409
            status_code = CONFLICT
            return status_code, False
        stored_post_number = post_inserter.define_stored_post_number()
        if stored_post_number >= 1000:
            NOT_FOUND = 404
            status_code = NOT_FOUND
            return status_code, False
        post_inserter.insert_post_into_db()
        CREATED = 201
        status_code = CREATED
        return status_code, stored_post_number + 1
