from utils import define_path_to_file, posts_list_is_ready_check, replace_reddit_by_test_file, restore_pre_test_state
import json
import os
import requests
import unittest


class TestDataCollection:
    """Contains data which will be used in unittests"""
    existent_post_dict = {'UNIQUE_ID': '48dde13e404611eb9360036bb7a2b36b',
                          'post URL': 'https://www.reddit.com/r/blog/comments/k967mm/reddit_in_2020/',
                          'username': 'reddit_irl', 'user karma': '197,182', 'user cake day': 'April 30, 2020',
                          'post karma': '18,395', 'comment karma': '11,835', 'post date': '09.12.2020',
                          'number of comments': '8.9k', 'number of votes': '168k', 'post category': 'blog'}
    nonexistent_post_dict = {'UNIQUE_ID': '00dde13e404611eb9360036bb7a2b36b',
                             'post URL': 'https://www.reddit.com/r/blog/comments/k967mm/reddit_in_2020/',
                             'username': 'reddit_irl', 'user karma': '197,182', 'user cake day': 'April 30, 2020',
                             'post karma': '18,395', 'comment karma': '11,835', 'post date': '09.12.2020',
                             'number of comments': '8.9k', 'number of votes': '168k', 'post category': 'blog'}
    incorrect_post_dict = {'UNIQUE_ID': '48dde13e404611eb9360036bb7a2b36b'}
    WAIT_RESPONSE_SECONDS = 5
    REDDIT_FILENAME_PREFIX = 'reddit-'
    REDDIT_TEST_FILENAME = "reddit-201901191955.txt"
    URL_WITHOUT_ID = "http://localhost:8087/posts/"
    URL_WITH_EXISTENT_ID = "http://localhost:8087/posts/48dde13e404611eb9360036bb7a2b36b/"
    URL_WITH_NONEXISTENT_ID = "http://localhost:8087/posts/00dde13e404611eb9360036bb7a2b36b/"
    INVALID_URL = "http://localhost:8087/posts/invalid/"


class DirReorganizerMixin:
    def setUp(self):
        """Defines setUp behavior for unittests. Calls the function that replaces reddit-file by test-file"""
        replace_reddit_by_test_file(TestDataCollection.REDDIT_TEST_FILENAME)

    def tearDown(self):
        """Defines tearDown behavior for unittests. Calls the function that restores pre-test state of the directory"""
        restore_pre_test_state(TestDataCollection.REDDIT_TEST_FILENAME)


class TestGET(DirReorganizerMixin, unittest.TestCase):
    def test_get_posts_success(self):
        print('testing get_posts success')
        req = requests.get(TestDataCollection.URL_WITHOUT_ID, timeout=TestDataCollection.WAIT_RESPONSE_SECONDS)
        expected_post_dict = TestDataCollection.existent_post_dict
        OK = 200
        self.assertEqual((req.status_code, req.json()[1]), (OK, expected_post_dict))

    def test_get_posts_no_file(self):
        print('testing get_posts with no file detected')
        path_to_reddit_file = define_path_to_file(TestDataCollection.REDDIT_FILENAME_PREFIX, os.path.dirname(__file__))
        os.remove(path_to_reddit_file)
        req = requests.get(TestDataCollection.URL_WITHOUT_ID, timeout=TestDataCollection.WAIT_RESPONSE_SECONDS)
        NOT_FOUND = 404
        self.assertEqual((req.status_code, req.content), (NOT_FOUND, b''))

    def test_get_posts_empty_file(self):
        print('testing get_posts with empty file')
        path_to_reddit_file = define_path_to_file(TestDataCollection.REDDIT_FILENAME_PREFIX, os.path.dirname(__file__))
        with open(path_to_reddit_file, 'w') as file:
            file.write('')
        req = requests.get(TestDataCollection.URL_WITHOUT_ID, timeout=TestDataCollection.WAIT_RESPONSE_SECONDS)
        NOT_FOUND = 404
        self.assertEqual((req.status_code, req.content), (NOT_FOUND, b''))

    def test_get_line_success(self):
        print('testing get_line success')
        req = requests.get(TestDataCollection.URL_WITH_EXISTENT_ID, timeout=TestDataCollection.WAIT_RESPONSE_SECONDS)
        expected_post_dict = TestDataCollection.existent_post_dict
        OK = 200
        self.assertEqual((req.status_code, req.json()), (OK, expected_post_dict))

    def test_get_line_no_file(self):
        print('testing get_line with no file detected')
        path_to_reddit_file = define_path_to_file(TestDataCollection.REDDIT_FILENAME_PREFIX, os.path.dirname(__file__))
        os.remove(path_to_reddit_file)
        req = requests.get(TestDataCollection.URL_WITH_NONEXISTENT_ID, timeout=TestDataCollection.WAIT_RESPONSE_SECONDS)
        NOT_FOUND = 404
        self.assertEqual((req.status_code, req.content), (NOT_FOUND, b''))

    def test_get_line_empty_file(self):
        print('testing get_posts with empty file')
        path_to_reddit_file = define_path_to_file(TestDataCollection.REDDIT_FILENAME_PREFIX, os.path.dirname(__file__))
        with open(path_to_reddit_file, 'w') as file:
            file.write('')
        req = requests.get(TestDataCollection.URL_WITH_NONEXISTENT_ID, timeout=TestDataCollection.WAIT_RESPONSE_SECONDS)
        NOT_FOUND = 404
        self.assertEqual((req.status_code, req.content), (NOT_FOUND, b''))

    def test_get_line_not_found(self):
        print('testing get_line not found')
        req = requests.get(TestDataCollection.URL_WITH_NONEXISTENT_ID, timeout=TestDataCollection.WAIT_RESPONSE_SECONDS)
        NOT_FOUND = 404
        self.assertEqual((req.status_code, req.content), (NOT_FOUND, b''))

    def test_get_url_not_valid(self):
        print('testing get_url is not valid')
        req = requests.get(TestDataCollection.INVALID_URL, timeout=TestDataCollection.WAIT_RESPONSE_SECONDS)
        NOT_FOUND = 404
        self.assertEqual((req.status_code, req.content), (NOT_FOUND, b''))


class TestPOST(DirReorganizerMixin, unittest.TestCase):
    def test_add_line_success(self):
        print('testing add_line success')
        post_data = TestDataCollection.nonexistent_post_dict
        post_data_json = json.dumps(post_data)
        req = requests.post(TestDataCollection.URL_WITHOUT_ID, data=post_data_json,
                            timeout=TestDataCollection.WAIT_RESPONSE_SECONDS)
        CREATED = 201
        INSERTED_LINE_NUMBER = 101
        self.assertEqual((req.status_code, req.json()), (CREATED, {'UNIQUE_ID': INSERTED_LINE_NUMBER}))

    def test_add_line_empty_file(self):
        print('testing add_line with empty file')
        path_to_reddit_file = define_path_to_file(TestDataCollection.REDDIT_FILENAME_PREFIX, os.path.dirname(__file__))
        with open(path_to_reddit_file, 'w') as file:
            file.write('')
        post_data = TestDataCollection.existent_post_dict
        post_data_json = json.dumps(post_data)
        req = requests.post(TestDataCollection.URL_WITHOUT_ID, data=post_data_json,
                            timeout=TestDataCollection.WAIT_RESPONSE_SECONDS)
        CREATED = 201
        INSERTED_LINE_NUMBER = 1
        self.assertEqual((req.status_code, req.json()), (CREATED, {'UNIQUE_ID': INSERTED_LINE_NUMBER}))

    def test_add_line_duplicate(self):
        print('testing add_line with duplicate')
        post_data = TestDataCollection.existent_post_dict
        post_data_json = json.dumps(post_data)
        req = requests.post(TestDataCollection.URL_WITHOUT_ID, data=post_data_json,
                            timeout=TestDataCollection.WAIT_RESPONSE_SECONDS)
        CONFLICT = 409
        self.assertEqual((req.status_code, req.content), (CONFLICT, b''))

    def test_add_line_incorrect_post_data(self):
        print('testing add_line with incorrect data')
        post_data = TestDataCollection.incorrect_post_dict
        post_data_json = json.dumps(post_data)
        req = requests.post(TestDataCollection.URL_WITHOUT_ID, data=post_data_json,
                            timeout=TestDataCollection.WAIT_RESPONSE_SECONDS)
        NOT_FOUND = 404
        self.assertEqual((req.status_code, req.content), (NOT_FOUND, b''))

    def test_post_url_not_valid(self):
        print('testing post_url is not valid')
        post_data = TestDataCollection.existent_post_dict
        post_data_json = json.dumps(post_data)
        req = requests.post(TestDataCollection.INVALID_URL, data=post_data_json,
                            timeout=TestDataCollection.WAIT_RESPONSE_SECONDS)
        NOT_FOUND = 404
        self.assertEqual((req.status_code, req.content), (NOT_FOUND, b''))


class TestDELETE(DirReorganizerMixin, unittest.TestCase):
    def test_del_line_success(self):
        print('testing del_line success')
        req = requests.delete(TestDataCollection.URL_WITH_EXISTENT_ID, timeout=TestDataCollection.WAIT_RESPONSE_SECONDS)
        OK = 200
        self.assertEqual(req.status_code, OK)

    def test_del_line_no_file(self):
        print('testing del_line with no file detected')
        path_to_reddit_file = define_path_to_file(TestDataCollection.REDDIT_FILENAME_PREFIX, os.path.dirname(__file__))
        os.remove(path_to_reddit_file)
        req = requests.delete(TestDataCollection.URL_WITH_NONEXISTENT_ID,
                              timeout=TestDataCollection.WAIT_RESPONSE_SECONDS)
        NOT_FOUND = 404
        self.assertEqual(req.status_code, NOT_FOUND)

    def test_del_line_empty_file(self):
        print('testing del_line with empty file')
        path_to_reddit_file = define_path_to_file(TestDataCollection.REDDIT_FILENAME_PREFIX, os.path.dirname(__file__))
        with open(path_to_reddit_file, 'w') as file:
            file.write('')
        req = requests.delete(TestDataCollection.URL_WITH_NONEXISTENT_ID,
                              timeout=TestDataCollection.WAIT_RESPONSE_SECONDS)
        NOT_FOUND = 404
        self.assertEqual(req.status_code, NOT_FOUND)

    def test_del_line_not_found(self):
        print('testing del_line not found')
        req = requests.delete(TestDataCollection.URL_WITH_NONEXISTENT_ID,
                              timeout=TestDataCollection.WAIT_RESPONSE_SECONDS)
        NOT_FOUND = 404
        self.assertEqual(req.status_code, NOT_FOUND)

    def test_delete_url_not_valid(self):
        print('testing delete_url is not valid')
        req = requests.delete(TestDataCollection.INVALID_URL, timeout=TestDataCollection.WAIT_RESPONSE_SECONDS)
        NOT_FOUND = 404
        self.assertEqual(req.status_code, NOT_FOUND)


class TestPUT(DirReorganizerMixin, unittest.TestCase):
    def test_change_line_success(self):
        print('testing change_line success')
        post_data = TestDataCollection.nonexistent_post_dict
        post_data_json = json.dumps(post_data)
        req = requests.put(TestDataCollection.URL_WITH_EXISTENT_ID, data=post_data_json,
                           timeout=TestDataCollection.WAIT_RESPONSE_SECONDS)
        OK = 200
        self.assertEqual(req.status_code, OK)

    def test_change_line_no_file(self):
        print('testing change_line with no file detected')
        path_to_reddit_file = define_path_to_file(TestDataCollection.REDDIT_FILENAME_PREFIX, os.path.dirname(__file__))
        os.remove(path_to_reddit_file)
        post_data = TestDataCollection.nonexistent_post_dict
        post_data_json = json.dumps(post_data)
        req = requests.put(TestDataCollection.URL_WITH_NONEXISTENT_ID, data=post_data_json,
                           timeout=TestDataCollection.WAIT_RESPONSE_SECONDS)
        NOT_FOUND = 404
        self.assertEqual(req.status_code, NOT_FOUND)

    def test_change_line_empty_file(self):
        print('testing change_line with empty file')
        path_to_reddit_file = define_path_to_file(TestDataCollection.REDDIT_FILENAME_PREFIX, os.path.dirname(__file__))
        with open(path_to_reddit_file, 'w') as file:
            file.write('')
        post_data = TestDataCollection.existent_post_dict
        post_data_json = json.dumps(post_data)
        req = requests.put(TestDataCollection.URL_WITH_NONEXISTENT_ID, data=post_data_json,
                           timeout=TestDataCollection.WAIT_RESPONSE_SECONDS)
        NOT_FOUND = 404
        self.assertEqual(req.status_code, NOT_FOUND)

    def test_change_line_duplicate(self):
        print('testing change_line with duplicate')
        post_data = TestDataCollection.existent_post_dict
        post_data_json = json.dumps(post_data)
        req = requests.put(TestDataCollection.URL_WITH_EXISTENT_ID, data=post_data_json,
                           timeout=TestDataCollection.WAIT_RESPONSE_SECONDS)
        CONFLICT = 409
        self.assertEqual(req.status_code, CONFLICT)

    def test_change_line_incorrect_put_data(self):
        print('testing change_line with incorrect data')
        post_data = TestDataCollection.incorrect_post_dict
        post_data_json = json.dumps(post_data)
        req = requests.put(TestDataCollection.URL_WITH_EXISTENT_ID, data=post_data_json,
                           timeout=TestDataCollection.WAIT_RESPONSE_SECONDS)
        NOT_FOUND = 404
        self.assertEqual(req.status_code, NOT_FOUND)

    def test_change_line_not_found(self):
        print('testing change_line not found')
        post_data = TestDataCollection.existent_post_dict
        post_data_json = json.dumps(post_data)
        req = requests.put(TestDataCollection.URL_WITH_NONEXISTENT_ID, data=post_data_json,
                           timeout=TestDataCollection.WAIT_RESPONSE_SECONDS)
        NOT_FOUND = 404
        self.assertEqual(req.status_code, NOT_FOUND)

    def test_put_url_not_valid(self):
        print('testing put_url is not valid')
        post_data = TestDataCollection.existent_post_dict
        post_data_json = json.dumps(post_data)
        req = requests.put(TestDataCollection.INVALID_URL, data=post_data_json,
                           timeout=TestDataCollection.WAIT_RESPONSE_SECONDS)
        NOT_FOUND = 404
        self.assertEqual(req.status_code, NOT_FOUND)


class TestListGeneratedByThreads(unittest.TestCase):
    def test_ordered_list(self):
        print('testing posts_list_is_ready_check using ordered list')
        ordered_posts_list = [
            {'post_index': 0, 'another_key': ''},
            {'post_index': 1},
            {'post_index': 2},
            {'post_index': 3, 'another_key': ''},
            {'post_index': 4},
            {'post_index': 5, 'another_key': ''},
        ]
        UNREACHABLE_NUMBER = 10
        stop_count = UNREACHABLE_NUMBER

        sliced_posts_list = ordered_posts_list[:0]
        needed_posts_count = 0
        list_is_ready = posts_list_is_ready_check(sliced_posts_list, needed_posts_count, stop_count)
        self.assertEqual(list_is_ready, False)

        needed_posts_count = 1
        list_is_ready = posts_list_is_ready_check(sliced_posts_list, needed_posts_count, stop_count)
        self.assertEqual(list_is_ready, False)

        sliced_posts_list = ordered_posts_list[:1]
        needed_posts_count = 1
        list_is_ready = posts_list_is_ready_check(sliced_posts_list, needed_posts_count, stop_count)
        self.assertEqual(list_is_ready, True)

        needed_posts_count = 2
        list_is_ready = posts_list_is_ready_check(sliced_posts_list, needed_posts_count, stop_count)
        self.assertEqual(list_is_ready, False)

        sliced_posts_list = ordered_posts_list[:2]
        needed_posts_count = 1
        list_is_ready = posts_list_is_ready_check(sliced_posts_list, needed_posts_count, stop_count)
        self.assertEqual(list_is_ready, True)

        needed_posts_count = 2
        list_is_ready = posts_list_is_ready_check(sliced_posts_list, needed_posts_count, stop_count)
        self.assertEqual(list_is_ready, False)

        sliced_posts_list = ordered_posts_list[:3]
        needed_posts_count = 2
        list_is_ready = posts_list_is_ready_check(sliced_posts_list, needed_posts_count, stop_count)
        self.assertEqual(list_is_ready, False)

        sliced_posts_list = ordered_posts_list[:4]
        needed_posts_count = 2
        list_is_ready = posts_list_is_ready_check(sliced_posts_list, needed_posts_count, stop_count)
        self.assertEqual(list_is_ready, True)

        needed_posts_count = 3
        list_is_ready = posts_list_is_ready_check(sliced_posts_list, needed_posts_count, stop_count)
        self.assertEqual(list_is_ready, False)

        sliced_posts_list = ordered_posts_list[:5]
        needed_posts_count = 2
        list_is_ready = posts_list_is_ready_check(sliced_posts_list, needed_posts_count, stop_count)
        self.assertEqual(list_is_ready, True)

        needed_posts_count = 3
        list_is_ready = posts_list_is_ready_check(sliced_posts_list, needed_posts_count, stop_count)
        self.assertEqual(list_is_ready, False)

        sliced_posts_list = ordered_posts_list[:]
        needed_posts_count = 3
        list_is_ready = posts_list_is_ready_check(sliced_posts_list, needed_posts_count, stop_count)
        self.assertEqual(list_is_ready, True)

    def test_unordered_list(self):
        print('testing posts_list_is_ready_check using unordered list')
        unordered_posts_list = [
            {'post_index': 0, 'another_key': ''},
            {'post_index': 1, 'another_key': ''},
            {'post_index': 3, 'another_key': ''},
            {'post_index': 4, 'another_key': ''},
        ]
        UNREACHABLE_NUMBER = 10
        stop_count = UNREACHABLE_NUMBER

        sliced_posts_list = unordered_posts_list[:1]
        needed_posts_count = 1
        list_is_ready = posts_list_is_ready_check(sliced_posts_list, needed_posts_count, stop_count)
        self.assertEqual(list_is_ready, True)

        sliced_posts_list = unordered_posts_list[:2]
        needed_posts_count = 2
        list_is_ready = posts_list_is_ready_check(sliced_posts_list, needed_posts_count, stop_count)
        self.assertEqual(list_is_ready, True)

        sliced_posts_list = unordered_posts_list[:3]
        needed_posts_count = 2
        list_is_ready = posts_list_is_ready_check(sliced_posts_list, needed_posts_count, stop_count)
        self.assertEqual(list_is_ready, True)

        needed_posts_count = 3
        list_is_ready = posts_list_is_ready_check(sliced_posts_list, needed_posts_count, stop_count)
        self.assertEqual(list_is_ready, False)

        sliced_posts_list = unordered_posts_list[:4]
        needed_posts_count = 2
        list_is_ready = posts_list_is_ready_check(sliced_posts_list, needed_posts_count, stop_count)
        self.assertEqual(list_is_ready, True)

        needed_posts_count = 3
        list_is_ready = posts_list_is_ready_check(sliced_posts_list, needed_posts_count, stop_count)
        self.assertEqual(list_is_ready, False)


def test_outcome_file(filename):
    """Defines whether reddit-file is correct. If each line of this file contains exactly 11 values

    and the number of lines is equal to 100, returns True. If the file is incorrect, returns False.
    """
    path_to_file = os.path.join(os.path.dirname(__file__), filename)
    if not os.path.exists(path_to_file):
        ERROR_TEXT = "File with the specified name doesn't exist"
        return ERROR_TEXT
    with open(path_to_file) as file:
        line_content = file.readline()
        lines_count = 0
        NEEDED_RECORDS_COUNT_PER_LINE = 11
        while line_content:
            line_data_list = line_content.split(';')
            if not len(line_data_list) == NEEDED_RECORDS_COUNT_PER_LINE:
                return False
            line_content = file.readline()
            lines_count += 1
    NEEDED_LINES_COUNT_IN_FILE = 100
    return lines_count == NEEDED_LINES_COUNT_IN_FILE


if __name__ == "__main__":
    unittest.main()
