from reddit_parser import FileWriter, PostsProcessor
from utils import check_duplicates, DataConverter
import json


def get_posts():
    """GET http://localhost:8087/posts/"""
    file_path = FileWriter.define_path_to_file()
    posts = []
    status_code = 404
    if file_path:
        with open(file_path) as file:
            for line in file:
                post_dict = DataConverter.make_dict_from_str(line)
                posts.append(post_dict)
        status_code = 200
    if not posts:
        return {'status_code': status_code}
    content = json.dumps(posts)
    return {'status_code': status_code, 'content': content}


def get_line(line_number):
    """GET http://localhost:8087/posts/12/"""
    file_path = FileWriter.define_path_to_file()
    post_dict = {}
    status_code = 404
    if file_path:
        with open(file_path) as file:
            current_line = 1
            for line in file:
                if current_line == line_number:
                    post_dict = DataConverter.make_dict_from_str(line)
                    status_code = 200
                    break
                current_line += 1
    if not post_dict:
        return {'status_code': status_code}
    content = json.dumps(post_dict)
    return {'status_code': status_code, 'content': content}


def add_line(post_dict):
    """POST http://localhost:8087/posts/"""
    file_path = FileWriter.define_path_to_file()
    posts_list = []
    status_code = 404
    if not file_path:
        PostsProcessor("https://www.reddit.com/top/?t=month", 100)
        file_path = FileWriter.define_path_to_file()
    post_dict = json.loads(post_dict)
    if len(post_dict) == 11:
        post_data_str = DataConverter.make_str_from_dict(post_dict)
        posts_list = open(file_path).readlines()
        if check_duplicates(post_data_str, posts_list):
            posts_list[len(posts_list) - 1] += '\n'
            posts_list.append(post_data_str)
            with open(file_path, 'w') as file:
                file.writelines(posts_list)
            status_code = 201
    if not status_code == 201:
        return {'status_code': status_code}
    content = json.dumps({'line_number': len(posts_list)})
    return {'status_code': status_code, 'content': content}


def del_line(line_number):
    """DELETE http://localhost:8087/posts/12/"""
    file_path = FileWriter.define_path_to_file()
    status_code = 404
    if file_path:
        posts_list = open(file_path).readlines()
        if len(posts_list) >= line_number and line_number:
            del posts_list[line_number - 1]
            if posts_list:
                posts_list[len(posts_list) - 1] = posts_list[len(posts_list) - 1].replace('\n', '')
            with open(file_path, 'w') as file:
                file.writelines(posts_list)
            status_code = 200
    return {'status_code': status_code}


def change_line(line_number, post_dict):
    """PUT http://localhost:8087/posts/12/"""
    file_path = FileWriter.define_path_to_file()
    status_code = 404
    if file_path:
        post_dict = json.loads(post_dict)
        if len(post_dict) == 11:
            posts_list = open(file_path).readlines()
            if len(posts_list) >= line_number and line_number:
                post_data_str = DataConverter.make_str_from_dict(post_dict)
                if line_number != len(posts_list):
                    post_data_str += '\n'
                stored_str = posts_list[line_number - 1]
                if stored_str != post_data_str:
                    posts_list[line_number - 1] = post_data_str
                    with open(file_path, 'w') as file:
                        file.writelines(posts_list)
                    status_code = 200
    return {'status_code': status_code}
