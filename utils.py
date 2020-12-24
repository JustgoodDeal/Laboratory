import datetime


class DataConverter:
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

    @staticmethod
    def convert_date_from_words_to_numbers(date_str):
        try:
            date_str = datetime.datetime.strptime(date_str, '%B %d, %Y').strftime('%d.%m.%Y')
        except ValueError:
            ...
        return date_str

    @staticmethod
    def convert_documents_into_post_dict(documents):
        post_dict = {}
        entity_order = ['post', 'user']
        for ind in range(2):
            entity_dict = documents[ind]
            del entity_dict['_id']
            entity_name = entity_order[ind]
            post_dict[entity_name] = entity_dict
        return post_dict


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
