from reddit_parser import FileWriter
from shutil import copy2
import json
import os
import requests
import unittest


class FileReplacer:
    reddit_test_file_name = "reddit-201901191955.txt"

    def replace_reddit_by_test_file(self):
        """Replaces reddit-file by test-file. Copies existing reddit-file to temporary while maintaining

        its original name, keeping it in the name of the temporary file.
        Removes reddit-file and copies test-file to the file with specified name.
        If initially reddit-file didn't exist the creation of temporary file is skipped.
        """
        path_to_reddit_file = FileWriter.define_path_to_file('reddit-')
        if path_to_reddit_file:
            chars_count_to_skip = len('reddit-')
            reddit_f_datetime_start_ind = path_to_reddit_file.rfind('reddit-') + chars_count_to_skip
            reddit_f_datetime = path_to_reddit_file[reddit_f_datetime_start_ind:]
            copy2(path_to_reddit_file, f'temp-{reddit_f_datetime}')
            os.remove(path_to_reddit_file)
        path_to_test_file = FileWriter.define_path_to_file('test-')
        copy2(path_to_test_file, self.reddit_test_file_name)

    def restore_pre_test_state(self):
        """Restores pre-test state of the directory. If tested file with specified name exists, removes it.

        If temporary file exists, defines original name of reddit-file, copies this file to the file
        with found name and removes temporary file.
        """
        if os.path.exists(self.reddit_test_file_name):
            os.remove(self.reddit_test_file_name)
        path_to_temp_file = FileWriter.define_path_to_file('temp-')
        if path_to_temp_file:
            chars_count_to_skip = len('temp-')
            former_reddit_f_datetime_start_ind = path_to_temp_file.rfind('temp-') + chars_count_to_skip
            former_reddit_f_datetime = path_to_temp_file[former_reddit_f_datetime_start_ind:]
            copy2(path_to_temp_file, f'reddit-{former_reddit_f_datetime}')
            os.remove(path_to_temp_file)


class DirReorganizerMixin:
    def setUp(self):
        """Defines setUp behavior for unittests. Calls the function that replaces reddit-file by test-file"""
        FileReplacer().replace_reddit_by_test_file()

    def tearDown(self):
        """Defines setUp behavior for unittests. Calls the function that restores pre-test state of the directory"""
        FileReplacer().restore_pre_test_state()


class PostDataCollection:
    """Contains post dictionaries that will be used in unittests"""
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


class TestGET(DirReorganizerMixin, unittest.TestCase):
    def test_get_posts_success(self):
        print('testing get_posts success')
        req = requests.get("http://localhost:8087/posts/", timeout=5)
        expected_post_dict = PostDataCollection.existent_post_dict
        self.assertEqual((req.status_code, req.json()[1]), (200, expected_post_dict))

    def test_get_posts_no_file(self):
        print('testing get_posts with no file detected')
        path_to_reddit_file = FileWriter.define_path_to_file('reddit-')
        os.remove(path_to_reddit_file)
        req = requests.get("http://localhost:8087/posts/", timeout=5)
        self.assertEqual((req.status_code, req.content), (404, b''))

    def test_get_posts_empty_file(self):
        print('testing get_posts with empty file')
        path_to_reddit_file = FileWriter.define_path_to_file('reddit-')
        with open(path_to_reddit_file, 'w') as file:
            file.write('')
        req = requests.get("http://localhost:8087/posts/", timeout=5)
        self.assertEqual((req.status_code, req.content), (404, b''))

    def test_get_line_success(self):
        print('testing get_line success')
        req = requests.get("http://localhost:8087/posts/48dde13e404611eb9360036bb7a2b36b/", timeout=5)
        expected_post_dict = PostDataCollection.existent_post_dict
        self.assertEqual((req.status_code, req.json()), (200, expected_post_dict))

    def test_get_line_no_file(self):
        print('testing get_line with no file detected')
        path_to_reddit_file = FileWriter.define_path_to_file('reddit-')
        os.remove(path_to_reddit_file)
        req = requests.get("http://localhost:8087/posts/48dde13e404611eb9360036bb7a2b36b/", timeout=5)
        self.assertEqual((req.status_code, req.content), (404, b''))

    def test_get_line_empty_file(self):
        print('testing get_posts with empty file')
        path_to_reddit_file = FileWriter.define_path_to_file('reddit-')
        with open(path_to_reddit_file, 'w') as file:
            file.write('')
        req = requests.get("http://localhost:8087/posts/48dde13e404611eb9360036bb7a2b36b/", timeout=5)
        self.assertEqual((req.status_code, req.content), (404, b''))

    def test_get_line_not_found(self):
        print('testing get_line not found')
        req = requests.get("http://localhost:8087/posts/00dde13e404611eb9360036bb7a2b36b/", timeout=5)
        self.assertEqual((req.status_code, req.content), (404, b''))

    def test_get_url_not_valid(self):
        print('testing get_url is not valid')
        req = requests.get("http://localhost:8087/posts/000dde13e404611eb9360036bb7a2b36b/", timeout=5)
        self.assertEqual((req.status_code, req.content), (404, b''))


class TestPOST(DirReorganizerMixin, unittest.TestCase):
    def test_add_line_success(self):
        print('testing add_line success')
        post_data = PostDataCollection.nonexistent_post_dict
        post_data_json = json.dumps(post_data)
        req = requests.post("http://localhost:8087/posts/", data=post_data_json, timeout=5)
        self.assertEqual((req.status_code, req.json()), (201, {'UNIQUE_ID': 101}))

    def test_add_line_empty_file(self):
        print('testing add_line with empty file')
        path_to_reddit_file = FileWriter.define_path_to_file('reddit-')
        with open(path_to_reddit_file, 'w') as file:
            file.write('')
        post_data = PostDataCollection.existent_post_dict
        post_data_json = json.dumps(post_data)
        req = requests.post("http://localhost:8087/posts/", data=post_data_json, timeout=5)
        self.assertEqual((req.status_code, req.json()), (201, {'UNIQUE_ID': 1}))

    def test_add_line_duplicate(self):
        print('testing add_line with duplicate')
        post_data = PostDataCollection.existent_post_dict
        post_data_json = json.dumps(post_data)
        req = requests.post("http://localhost:8087/posts/", data=post_data_json, timeout=5)
        self.assertEqual((req.status_code, req.content), (409, b''))

    def test_add_line_incorrect_post_data(self):
        print('testing add_line with incorrect data')
        post_data = PostDataCollection.incorrect_post_dict
        post_data_json = json.dumps(post_data)
        req = requests.post("http://localhost:8087/posts/", data=post_data_json, timeout=5)
        self.assertEqual((req.status_code, req.content), (404, b''))

    def test_post_url_not_valid(self):
        print('testing post_url is not valid')
        post_data = PostDataCollection.existent_post_dict
        post_data_json = json.dumps(post_data)
        req = requests.post("http://localhost:8087/postsinvalid/", data=post_data_json, timeout=5)
        self.assertEqual((req.status_code, req.content), (404, b''))


class TestDELETE(DirReorganizerMixin, unittest.TestCase):
    def test_del_line_success(self):
        print('testing del_line success')
        req = requests.delete("http://localhost:8087/posts/48dde13e404611eb9360036bb7a2b36b/", timeout=5)
        self.assertEqual(req.status_code, 200)

    def test_del_line_no_file(self):
        print('testing del_line with no file detected')
        path_to_reddit_file = FileWriter.define_path_to_file('reddit-')
        os.remove(path_to_reddit_file)
        req = requests.delete("http://localhost:8087/posts/48dde13e404611eb9360036bb7a2b36b/", timeout=5)
        self.assertEqual(req.status_code, 404)

    def test_del_line_empty_file(self):
        print('testing del_line with empty file')
        path_to_reddit_file = FileWriter.define_path_to_file('reddit-')
        with open(path_to_reddit_file, 'w') as file:
            file.write('')
        req = requests.delete("http://localhost:8087/posts/48dde13e404611eb9360036bb7a2b36b/", timeout=5)
        self.assertEqual(req.status_code, 404)

    def test_del_line_not_found(self):
        print('testing del_line not found')
        req = requests.delete("http://localhost:8087/posts/00dde13e404611eb9360036bb7a2b36b/", timeout=5)
        self.assertEqual(req.status_code, 404)

    def test_delete_url_not_valid(self):
        print('testing delete_url is not valid')
        req = requests.delete("http://localhost:8087/posts/48dde13e404611eb9360036bb7a2b36b/del", timeout=5)
        self.assertEqual(req.status_code, 404)


class TestPUT(DirReorganizerMixin, unittest.TestCase):
    def test_change_line_success(self):
        print('testing change_line success')
        post_data = PostDataCollection.nonexistent_post_dict
        post_data_json = json.dumps(post_data)
        url = "http://localhost:8087/posts/48dde13e404611eb9360036bb7a2b36b/"
        req = requests.put(url, data=post_data_json, timeout=5)
        self.assertEqual(req.status_code, 200)

    def test_change_line_no_file(self):
        print('testing change_line with no file detected')
        path_to_reddit_file = FileWriter.define_path_to_file('reddit-')
        os.remove(path_to_reddit_file)
        post_data = PostDataCollection.nonexistent_post_dict
        post_data_json = json.dumps(post_data)
        url = "http://localhost:8087/posts/48dde13e404611eb9360036bb7a2b36b/"
        req = requests.put(url, data=post_data_json, timeout=5)
        self.assertEqual(req.status_code, 404)

    def test_change_line_empty_file(self):
        print('testing change_line with empty file')
        path_to_reddit_file = FileWriter.define_path_to_file('reddit-')
        with open(path_to_reddit_file, 'w') as file:
            file.write('')
        post_data = PostDataCollection.existent_post_dict
        post_data_json = json.dumps(post_data)
        url = "http://localhost:8087/posts/48dde13e404611eb9360036bb7a2b36b/"
        req = requests.put(url, data=post_data_json, timeout=5)
        self.assertEqual(req.status_code, 404)

    def test_change_line_duplicate(self):
        print('testing change_line with duplicate')
        post_data = PostDataCollection.existent_post_dict
        post_data_json = json.dumps(post_data)
        url = "http://localhost:8087/posts/48dde13e404611eb9360036bb7a2b36b/"
        req = requests.put(url, data=post_data_json, timeout=5)
        self.assertEqual(req.status_code, 409)

    def test_change_line_incorrect_put_data(self):
        print('testing change_line with incorrect data')
        post_data = PostDataCollection.incorrect_post_dict
        post_data_json = json.dumps(post_data)
        url = "http://localhost:8087/posts/48dde13e404611eb9360036bb7a2b36b/"
        req = requests.put(url, data=post_data_json, timeout=5)
        self.assertEqual(req.status_code, 404)

    def test_change_line_not_found(self):
        print('testing change_line not found')
        post_data = PostDataCollection.existent_post_dict
        post_data_json = json.dumps(post_data)
        url = "http://localhost:8087/posts/00dde13e404611eb9360036bb7a2b36b/"
        req = requests.put(url, data=post_data_json, timeout=5)
        self.assertEqual(req.status_code, 404)

    def test_put_url_not_valid(self):
        print('testing put_url is not valid')
        post_data = PostDataCollection.existent_post_dict
        post_data_json = json.dumps(post_data)
        url = "http://localhost:8087/posts/bug48dde13e404611eb9360036bb7a2b36b/"
        req = requests.put(url, data=post_data_json, timeout=5)
        self.assertEqual(req.status_code, 404)


def test_outcome_file(filename):
    """Defines whether reddit-file is correct. If each line of this file contains exactly 11 values

    and the number of lines is equal to 100, returns True. If the file is incorrect, returns False.
    """
    if os.path.exists(filename):
        with open(filename) as file:
            data = file.readline()
            lines_count = 0
            while data:
                data = data.split(';')
                if not len(data) == 11:
                    return
                data = file.readline()
                lines_count += 1
            return lines_count == 100
    return "File with the specified name doesn't exist"


if __name__ == "__main__":
    unittest.main()
