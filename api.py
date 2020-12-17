from reddit_parser import FileWriter, PostsProcessor
from utils import check_duplicates, DataConverter, find_line_index
import json


def get_posts():
    """GET http://localhost:8087/posts/"""
    file_path = FileWriter.define_path_to_file('reddit-')
    posts = []
    status_code = 404
    if file_path:
        with open(file_path) as file:
            for line in file:
                post_dict = DataConverter.make_dict_from_str(line)
                posts.append(post_dict)
        status_code = 200
    if not posts:
        status_code = 404
        return {'status_code': status_code}
    content = json.dumps(posts)
    return {'status_code': status_code, 'content': content}


def get_line(id):
    """GET http://localhost:8087/posts/bcfe98ba3eb111eba3a5896f760fd13c/"""
    file_path = FileWriter.define_path_to_file('reddit-')
    post_dict = {}
    status_code = 404
    if file_path:
        with open(file_path) as file:
            for line in file:
                if id in line:
                    post_dict = DataConverter.make_dict_from_str(line)
                    status_code = 200
                    break
    if not post_dict:
        return {'status_code': status_code}
    content = json.dumps(post_dict)
    return {'status_code': status_code, 'content': content}


def add_line(post_dict):
    """POST http://localhost:8087/posts/"""
    file_path = FileWriter.define_path_to_file('reddit-')
    posts_list = []
    status_code = 404
    if not file_path:
        PostsProcessor("https://www.reddit.com/top/?t=month", 100)
        file_path = FileWriter.define_path_to_file('reddit-')
    post_dict = json.loads(post_dict)
    if len(post_dict) == 11:
        post_data_str = DataConverter.make_str_from_dict(post_dict)
        posts_list = open(file_path).readlines()
        if check_duplicates(post_data_str, posts_list):
            if posts_list:
                posts_list[len(posts_list) - 1] += '\n'
            posts_list.append(post_data_str)
            with open(file_path, 'w') as file:
                file.writelines(posts_list)
            status_code = 201
        else:
            status_code = 409
    if not status_code == 201:
        return {'status_code': status_code}
    content = json.dumps({'UNIQUE_ID': len(posts_list)})
    return {'status_code': status_code, 'content': content}


def del_line(id):
    """DELETE http://localhost:8087/posts/bcfe98ba3eb111eba3a5896f760fd13c/"""
    file_path = FileWriter.define_path_to_file('reddit-')
    status_code = 404
    if file_path:
        posts_list = open(file_path).readlines()
        line_index = find_line_index(id, posts_list)
        if line_index:
            del posts_list[line_index]
            posts_list[len(posts_list) - 1] = posts_list[len(posts_list) - 1].replace('\n', '')
            with open(file_path, 'w') as file:
                file.writelines(posts_list)
            status_code = 200
    return {'status_code': status_code}


def change_line(id, post_dict):
    """PUT http://localhost:8087/posts/bcfe98ba3eb111eba3a5896f760fd13c/"""
    file_path = FileWriter.define_path_to_file('reddit-')
    status_code = 404
    if file_path:
        post_dict = json.loads(post_dict)
        if len(post_dict) == 11:
            posts_list = open(file_path).readlines()
            line_index = find_line_index(id, posts_list)
            if line_index:
                post_data_str = DataConverter.make_str_from_dict(post_dict)
                if post_data_str != posts_list[line_index].replace('\n', ''):
                    if line_index != len(posts_list):
                        post_data_str += '\n'
                    posts_list[line_index] = post_data_str
                    with open(file_path, 'w') as file:
                        file.writelines(posts_list)
                    status_code = 200
                else:
                    status_code = 409
    return {'status_code': status_code}
