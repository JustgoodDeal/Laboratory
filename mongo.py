from pymongo import MongoClient
from utils import DataConverter


class MongoExecutor:
    connection_entries = {
        'host': '127.0.0.1',
        'port': 27017
    }
    database_name = 'reddit_db'
    posts_collection_name = 'posts'
    users_collection_name = 'users'

    def __init__(self, posts_list=None, post_dict=None, unique_id=None):
        """Initializes connection to the MongoDB database on specified host and port.

        Gets posts and users collections. May take a list of each post data,
        a dictionary with post data or a unique id of the post.
        """
        self.client = MongoClient(**self.connection_entries)
        self.database = self.client[self.database_name]
        self.posts_collection = self.database[self.posts_collection_name]
        self.users_collection = self.database[self.users_collection_name]
        self.posts_list = posts_list
        self.post_dict = post_dict
        self.unique_id = unique_id

    def insert_all_posts_into_db(self):
        """Saves all posts data to the collections"""
        for post_dict in self.posts_list:
            self.post_dict = post_dict
            self.insert_post_into_db()

    def insert_post_into_db(self):
        """Saves post data to the collections"""
        self.posts_collection.insert_one(self.post_dict['post'])
        self.users_collection.insert_one(self.post_dict['user'])

    def get_all_posts_from_db(self):
        """Gets all posts data from a database. Converts each found post to a dictionary

        and adds to a list, which is returned. If no posts were found, returns None.
        """
        stored_posts = self.posts_collection.find({})
        if not stored_posts:
            return
        self.posts_list = []
        for post_data in stored_posts:
            self.unique_id = post_data['unique_id']
            user_data = self.get_user_data_from_db()
            stored_post_dict = DataConverter.convert_documents_into_post_dict([post_data, user_data])
            self.posts_list.append(stored_post_dict)
        return self.posts_list

    def get_post_from_db(self):
        """Gets post data from a database by post unique id. If post was found, returns a dictionary

        with converted post data. If post wasn't found, returns None.
        """
        post_data = self.get_post_data_from_db()
        if not post_data:
            return
        user_data = self.get_user_data_from_db()
        stored_post_dict = DataConverter.convert_documents_into_post_dict([post_data, user_data])
        return stored_post_dict

    def get_post_data_from_db(self):
        """Searches for a post in related collection"""
        query_dict = {'unique_id': self.unique_id}
        return self.posts_collection.find_one(query_dict)

    def get_user_data_from_db(self):
        """Searches for a user in related collection"""
        query_dict = {'post_unique_id': self.unique_id}
        return self.users_collection.find_one(query_dict)

    def define_stored_posts_number(self):
        """Defines current number of posts stored in a database"""
        stored_posts = self.posts_collection.find({})
        return stored_posts.count()

    def update_post(self):
        """Modifies post data records in related collections"""
        self.posts_collection.update_one({'unique_id': self.unique_id}, {'$set': self.post_dict['post']})
        self.users_collection.update_one({'post_unique_id': self.unique_id}, {'$set': self.post_dict['user']})

    def delete_post(self):
        """Tries to delete a post from a database by its unique id. Returns the number of deleted posts"""
        post_delete_result = self.posts_collection.delete_one({'unique_id': self.unique_id})
        user_delete_result = self.users_collection.delete_one({'post_unique_id': self.unique_id})
        deleted_documents_count = post_delete_result.deleted_count + user_delete_result.deleted_count
        return deleted_documents_count