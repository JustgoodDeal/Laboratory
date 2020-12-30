from postgre import PostgreAllPostsInserter, PostgreTablesCreator, PostgreTablesRemover, PostgreTablesTruncator, \
    PostgreQueryCollection
import json
import os
import requests
import unittest


class PostDataCollection:
    """Contains posts data that will be used in unittests"""
    init_post_dict_1 = {'username': 'PrettyCoolTim', 'user_karma': 312355, 'user_cake_day': '08.07.2020',
                        'post_karma': 200743, 'comment_karma': 3974, 'unique_id': '582ef18c485c11ebb1f1c9ee1740fa9b',
                        'post_url': 'https://www.reddit.com/r/memes/comments/khiyao/uncanny_resemblance/',
                        'post_date': '12.21.2020', 'comments_number': 495, 'votes_number': 190000,
                        'post_category': 'memes'}
    init_post_dict_2 = {'username': 'Wrobbo09', 'user_karma': 192593, 'user_cake_day': '03.31.2019',
                        'post_karma': 147453, 'comment_karma': 5649, 'unique_id': '5bcd0748485c11ebb1f1c9ee1740fa9b',
                        'post_url': 'https://www.reddit.com/r/memes/comments/kewn6p/oh_no_you_dont/',
                        'post_date': '12.17.2020', 'comments_number': 1400, 'votes_number': 174000,
                        'post_category': 'memes'}
    init_post_dict_3 = {'username': 'Morchel03', 'user_karma': 731820, 'user_cake_day': '01.17.2018',
                        'post_karma': 572765, 'comment_karma': 84803, 'unique_id': '5eee864a485c11ebb1f1c9ee1740fa9b',
                        'post_url': 'https://www.reddit.com/r/memes/comments/kjdwn1/oh_god_no/',
                        'post_date': '12.24.2020', 'comments_number': 1183, 'votes_number': 172000,
                        'post_category': 'memes'}
    init_posts_data = [init_post_dict_1, init_post_dict_2, init_post_dict_3]
    post_dict_1 = {'username': 'PrettyCoolTim', 'user_karma': 312355, 'user_cake_day': '07.08.2020',
                   'post_karma': 200743, 'comment_karma': 3974, 'unique_id': '582ef18c485c11ebb1f1c9ee1740fa9b',
                   'post_url': 'https://www.reddit.com/r/memes/comments/khiyao/uncanny_resemblance/',
                   'post_date': '21.12.2020', 'comments_number': 495, 'votes_number': 190000, 'post_category': 'memes'}
    post_dict_2 = {'username': 'Wrobbo09', 'user_karma': 192593, 'user_cake_day': '31.03.2019',
                   'post_karma': 147453, 'comment_karma': 5649, 'unique_id': '5bcd0748485c11ebb1f1c9ee1740fa9b',
                   'post_url': 'https://www.reddit.com/r/memes/comments/kewn6p/oh_no_you_dont/',
                   'post_date': '17.12.2020', 'comments_number': 1400, 'votes_number': 174000, 'post_category': 'memes'}
    post_dict_3 = {'username': 'Morchel03', 'user_karma': 731820, 'user_cake_day': '17.01.2018', 'post_karma': 572765,
                   'comment_karma': 84803, 'unique_id': '5eee864a485c11ebb1f1c9ee1740fa9b',
                   'post_url': 'https://www.reddit.com/r/memes/comments/kjdwn1/oh_god_no/', 'post_date': '24.12.2020',
                   'comments_number': 1183, 'votes_number': 172000, 'post_category': 'memes'}
    posts_data = [post_dict_1, post_dict_2, post_dict_3]
    nonexistent_post_dict = {'username': 'reddit_irl', 'user_karma': 197182, 'user_cake_day': '30.04.2020',
                             'post_karma': 18395, 'comment_karma': 11835,
                             'unique_id': '48dde13e404611eb9360036bb7a2b36b',
                             'post_url': 'https://www.reddit.com/r/blog/comments/k967mm/reddit_in_2020/',
                             'post_date': '27.11.2020', 'comments_number': 8900, 'votes_number': 168000,
                             'post_category': 'blog'}
    incorrect_post_dict = {'username': 'reddit_irl', 'user_karma': 197182, 'user_cake_day': '30.04.2020', }
    update_post_dict = {'username': 'NotPrettyCoolTim', 'user_karma': 312355, 'user_cake_day': '07.08.2020',
                        'post_karma': 200743, 'comment_karma': 3974, 'unique_id': '582ef18c485c11ebb1f1c9ee1740fa9b',
                        'post_url': 'https://www.reddit.com/r/memes/comments/khiyao/uncanny_resemblance/',
                        'post_date': '12.21.2020', 'comments_number': 495, 'votes_number': 190000,
                        'post_category': 'memes'}


class EnvironmentModifier:
    def prepare_test_environment(self):
        """Creates a file indicating that unittests are have been running at the moment.

        Creates 2 related test tables in a database, inserts certain test post data to the tables.
        """
        with open(PostgreQueryCollection.test_mode_identifier_filename, 'w') as file:
            file.write('')
        with PostgreTablesCreator() as tables_creator:
            tables_creator.create_tables()
        with PostgreAllPostsInserter(PostDataCollection.init_posts_data) as post_inserter:
            post_inserter.insert_all_posts_into_db()

    def restore_pre_test_state(self):
        """Restores pre-test state of the directory and database. Removes 2 related test tables

        from a database, deletes a file indicating that unittests are have been running at the moment.
        """
        with PostgreTablesRemover() as tables_remover:
            tables_remover.remove_tables()
        os.remove(PostgreQueryCollection.test_mode_identifier_filename)


class ReorganizerMixin:
    def setUp(self):
        """Defines setUp behavior for unittests. Calls the function that prepares test environment"""
        EnvironmentModifier().prepare_test_environment()

    def tearDown(self):
        """Defines tearDown behavior for unittests.

        Calls the function that restores pre-test state of the directory and database.
        """
        EnvironmentModifier().restore_pre_test_state()


class TestGET(ReorganizerMixin, unittest.TestCase):
    def test_get_posts_success(self):
        print('testing get_posts success')
        req = requests.get("http://localhost:8087/posts/", timeout=5)
        self.assertEqual((req.status_code, req.json()), (200, PostDataCollection.posts_data))

    def test_get_posts_no_table(self):
        print('testing get_posts with no table found')
        with PostgreTablesRemover() as tables_remover:
            tables_remover.remove_tables()
        req = requests.get("http://localhost:8087/posts/", timeout=5)
        self.assertEqual((req.status_code, req.content), (404, b''))

    def test_get_posts_empty_table(self):
        print('testing get_posts with empty table')
        with PostgreTablesTruncator() as tables_truncator:
            tables_truncator.truncate_tables()
        req = requests.get("http://localhost:8087/posts/", timeout=5)
        self.assertEqual((req.status_code, req.content), (404, b''))

    def test_get_post_success(self):
        print('testing get_post success')
        req = requests.get("http://localhost:8087/posts/582ef18c485c11ebb1f1c9ee1740fa9b/", timeout=5)
        self.assertEqual((req.status_code, req.json()), (200, PostDataCollection.post_dict_1))

    def test_get_post_no_table(self):
        print('testing get_post with no table found')
        with PostgreTablesRemover() as tables_remover:
            tables_remover.remove_tables()
        req = requests.get("http://localhost:8087/posts/582ef18c485c11ebb1f1c9ee1740fa9b/", timeout=5)
        self.assertEqual((req.status_code, req.content), (404, b''))

    def test_get_post_empty_table(self):
        print('testing get_post with empty table')
        with PostgreTablesTruncator() as tables_truncator:
            tables_truncator.truncate_tables()
        req = requests.get("http://localhost:8087/posts/582ef18c485c11ebb1f1c9ee1740fa9b/", timeout=5)
        self.assertEqual((req.status_code, req.content), (404, b''))

    def test_get_post_not_found(self):
        print('testing get_post not found')
        req = requests.get("http://localhost:8087/posts/002ef18c485c11ebb1f1c9ee1740fa9b/", timeout=5)
        self.assertEqual((req.status_code, req.content), (404, b''))

    def test_get_url_not_valid(self):
        print('testing get_url is not valid')
        req = requests.get("http://localhost:8087/posts/0582ef18c485c11ebb1f1c9ee1740fa9b/", timeout=5)
        self.assertEqual((req.status_code, req.content), (404, b''))


class TestPOST(ReorganizerMixin, unittest.TestCase):
    def test_add_post_success(self):
        print('testing add_post success')
        post_data = PostDataCollection.nonexistent_post_dict
        post_data_json = json.dumps(post_data)
        req = requests.post("http://localhost:8087/posts/", data=post_data_json, timeout=5)
        self.assertEqual((req.status_code, req.json()), (201, {'UNIQUE_ID': 4}))

    def test_add_post_empty_table(self):
        print('testing add_post with empty table')
        with PostgreTablesTruncator() as tables_truncator:
            tables_truncator.truncate_tables()
        post_data = PostDataCollection.post_dict_1
        post_data_json = json.dumps(post_data)
        req = requests.post("http://localhost:8087/posts/", data=post_data_json, timeout=5)
        self.assertEqual((req.status_code, req.json()), (201, {'UNIQUE_ID': 1}))

    def test_add_post_duplicate(self):
        print('testing add_post with duplicate')
        post_data = PostDataCollection.post_dict_1
        post_data_json = json.dumps(post_data)
        req = requests.post("http://localhost:8087/posts/", data=post_data_json, timeout=5)
        self.assertEqual((req.status_code, req.content), (409, b''))

    def test_add_post_incorrect_post_dict(self):
        print('testing add_post with incorrect post dict')
        post_data = PostDataCollection.incorrect_post_dict
        post_data_json = json.dumps(post_data)
        req = requests.post("http://localhost:8087/posts/", data=post_data_json, timeout=5)
        self.assertEqual((req.status_code, req.content), (404, b''))

    def test_post_url_not_valid(self):
        print('testing post_url is not valid')
        post_data = PostDataCollection.post_dict_1
        post_data_json = json.dumps(post_data)
        req = requests.post("http://localhost:8087/postsinvalid/", data=post_data_json, timeout=5)
        self.assertEqual((req.status_code, req.content), (404, b''))


class TestDELETE(ReorganizerMixin, unittest.TestCase):
    def test_del_post_success(self):
        print('testing del_post success')
        req = requests.delete("http://localhost:8087/posts/582ef18c485c11ebb1f1c9ee1740fa9b/", timeout=5)
        self.assertEqual(req.status_code, 200)

    def test_del_post_no_table(self):
        print('testing del_post with no table found')
        with PostgreTablesRemover() as tables_remover:
            tables_remover.remove_tables()
        req = requests.delete("http://localhost:8087/posts/582ef18c485c11ebb1f1c9ee1740fa9b/", timeout=5)
        self.assertEqual(req.status_code, 404)

    def test_del_post_empty_table(self):
        print('testing del_post with empty table')
        with PostgreTablesTruncator() as tables_truncator:
            tables_truncator.truncate_tables()
        req = requests.delete("http://localhost:8087/posts/582ef18c485c11ebb1f1c9ee1740fa9b/", timeout=5)
        self.assertEqual(req.status_code, 404)

    def test_del_post_not_found(self):
        print('testing del_post not found')
        req = requests.delete("http://localhost:8087/posts/002ef18c485c11ebb1f1c9ee1740fa9b/", timeout=5)
        self.assertEqual(req.status_code, 404)

    def test_delete_url_not_valid(self):
        print('testing delete_url is not valid')
        req = requests.delete("http://localhost:8087/posts/582ef18c485c11ebb1f1c9ee1740fa9b/del", timeout=5)
        self.assertEqual(req.status_code, 404)


class TestPUT(ReorganizerMixin, unittest.TestCase):
    def test_update_post_success(self):
        print('testing update_post success')
        post_data = PostDataCollection.update_post_dict
        post_data_json = json.dumps(post_data)
        url = "http://localhost:8087/posts/582ef18c485c11ebb1f1c9ee1740fa9b/"
        req = requests.put(url, data=post_data_json, timeout=5)
        self.assertEqual(req.status_code, 200)

    def test_update_post_no_table(self):
        print('testing update_post with no table found')
        with PostgreTablesRemover() as tables_remover:
            tables_remover.remove_tables()
        post_data = PostDataCollection.update_post_dict
        post_data_json = json.dumps(post_data)
        url = "http://localhost:8087/posts/582ef18c485c11ebb1f1c9ee1740fa9b/"
        req = requests.put(url, data=post_data_json, timeout=5)
        self.assertEqual(req.status_code, 404)

    def test_update_post_empty_table(self):
        print('testing update_post with empty table')
        with PostgreTablesTruncator() as tables_truncator:
            tables_truncator.truncate_tables()
        post_data = PostDataCollection.update_post_dict
        post_data_json = json.dumps(post_data)
        url = "http://localhost:8087/posts/582ef18c485c11ebb1f1c9ee1740fa9b/"
        req = requests.put(url, data=post_data_json, timeout=5)
        self.assertEqual(req.status_code, 404)

    def test_update_post_duplicate(self):
        print('testing update_post with duplicate')
        post_data = PostDataCollection.post_dict_1
        post_data_json = json.dumps(post_data)
        url = "http://localhost:8087/posts/582ef18c485c11ebb1f1c9ee1740fa9b/"
        req = requests.put(url, data=post_data_json, timeout=5)
        self.assertEqual(req.status_code, 409)

    def test_update_post_incorrect_put_data(self):
        print('testing update_post with incorrect data')
        post_data = PostDataCollection.incorrect_post_dict
        post_data_json = json.dumps(post_data)
        url = "http://localhost:8087/posts/582ef18c485c11ebb1f1c9ee1740fa9b/"
        req = requests.put(url, data=post_data_json, timeout=5)
        self.assertEqual(req.status_code, 404)

    def test_update_post_not_found(self):
        print('testing update_post not found')
        post_data = PostDataCollection.nonexistent_post_dict
        post_data_json = json.dumps(post_data)
        url = "http://localhost:8087/posts/48dde13e404611eb9360036bb7a2b36b/"
        req = requests.put(url, data=post_data_json, timeout=5)
        self.assertEqual(req.status_code, 404)

    def test_put_url_not_valid(self):
        print('testing put_url is not valid')
        post_data = PostDataCollection.post_dict_1
        post_data_json = json.dumps(post_data)
        url = "http://localhost:8087/posts/bug582ef18c485c11ebb1f1c9ee1740fa9b/"
        req = requests.put(url, data=post_data_json, timeout=5)
        self.assertEqual(req.status_code, 404)


if __name__ == "__main__":
    unittest.main()
