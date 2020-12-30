import datetime
import os


class DataConverter:
    @staticmethod
    def make_str_from_dict(post_dict):
        """Converts dictionary with post data to string"""
        post_data_str = ''
        for data_name in post_dict:
            data_value = post_dict[data_name]
            post_data_str += f'{data_value};'
        return post_data_str[:len(post_data_str) - 1]

    @staticmethod
    def make_dict_from_str(data_str):
        """Converts string with post data to dictionary in a specific sequence"""
        dict_order = ['UNIQUE_ID', 'post URL', 'username', 'user karma', 'user cake day', 'post karma', 'comment karma',
                      'post date', 'number of comments', 'number of votes', 'post category']
        post_data = data_str.replace('\n', '').split(';')
        post_dict = {}
        for ind in range(len(dict_order)):
            post_dict[dict_order[ind]] = post_data[ind]
        return post_dict

    @staticmethod
    def convert_time_lapse_to_date(date_str):
        """Takes a string containing time lapse between publishing post and current time.

        ('just now', '7 days ago', '1 month ago', etc.). Converts it to the date when the post was published.
        """
        if 'just now' in date_str or 'hour' in date_str:
            days = 0
        elif 'month' in date_str:
            days = 31
        else:
            days = int(date_str.split()[0])
        date = datetime.datetime.today() - datetime.timedelta(days=days)
        return date.strftime("%d.%m.%Y")


def define_path_to_file(prefix):
    """Defines path to the file existing in the directory under the prefix contained in the file name"""
    work_dir_path = os.getcwd()
    for name in os.listdir(work_dir_path):
        if os.path.isfile(name) and prefix in name:
            return os.path.join(work_dir_path, name)


def check_duplicates(post_data_str, posts_list):
    """Takes post data string and defines part of it being post unique id. If any of the strings from taken list

    contains the same unique id, returns None (duplicate found); otherwise, returns True (no duplicates).
    """
    sent_id = post_data_str[:32]
    for post_str in posts_list:
        stored_id = post_str[:32]
        if sent_id == stored_id:
            return
    return True


def find_line_index(sent_id, posts_list):
    """Takes post unique id. If is detected that one of the strings from taken

    list contains the same unique id, returns line index of this string.
    """
    for ind, post_str in enumerate(posts_list):
        stored_id = post_str[:32]
        if sent_id == stored_id:
            return ind
    return


def parse_url(url):
    """Parses provided URL. Define whether the URL contains 32-digits UNIQUE_ID. If true, returns this id.

    If the URL contains only the word "posts", returns None. If URL is incorrect, returns 404
    """
    latest_slash = url[len(url) - 1]
    if latest_slash == '/' and url[:5] == 'posts':
        id_start_index = 6
        if len(url) > id_start_index:
            id = url[id_start_index:len(url) - 1]
            if len(id) == 32:
                return id
            return 404
        return
    return 404
