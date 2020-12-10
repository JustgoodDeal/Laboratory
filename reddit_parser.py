from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
import datetime
import os
import requests
import time


class PostDivsDetector:
    def __call__(self, driver):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        post_divs_loaded = driver.find_elements_by_css_selector('div.rpBJOHq2PR60pnwJlUyP0 > div')
        if len(post_divs_loaded) > 100:
            page_text = driver.page_source
            page_text_soup = BeautifulSoup(page_text, features="html.parser")
            all_posts = page_text_soup.findAll('div', {"class": "_1oQyIsiPHYt6nx7VOmd1sz"})
            if len(all_posts) > 99:
                return all_posts[:100]
            else:
                return False
        else:
            return False


def get_html(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:45.0) Gecko/20100101 Firefox/45.0'
    }
    request_succeed = False
    while not request_succeed:
        try:
            response = requests.get(url, timeout=5, headers=headers)
            request_succeed = True
        except requests.exceptions.ReadTimeout:
            time.sleep(1)
    response.encoding = 'utf8'
    return response.text


driver = webdriver.Chrome()
driver.get("https://www.reddit.com/top/?t=month")
try:
    all_posts = WebDriverWait(driver, 20).until(PostDivsDetector())
finally:
    driver.quit()

parsed_post_data = []
for post in all_posts:
    try:
        post_dict = {}
        post_soup = BeautifulSoup(str(post), features="html.parser")

        date_and_url_a = post_soup.findAll('a', {"class": "_3jOxDPIQ0KaOWpzvSQo-1s"})[0]
        post_url = date_and_url_a.attrs["href"]
        post_date = date_and_url_a.text

        comments_number_spans = post_soup.findAll('span', {"class": "D6SuXeSnAAagG8dKAb4O4"})
        if comments_number_spans:
            comments_number_span = comments_number_spans[0]
            comments_number = comments_number_span.text
        else:
            comments_number_span = post_soup.findAll('span', {"class": "FHCV02u6Cp2zYL0fhQPsO"})[0]
            raw_text = comments_number_span.text
            space_index = raw_text.find(' ')
            comments_number = raw_text[:space_index]

        votes_number_div = post_soup.findAll('div', {"class": "_1rZYMD_4xY3gRcSS3p8ODO"})[1]
        votes_number = votes_number_div.text

        category_a = post_soup.findAll('a', {"class": "_3ryJoIoycVkA88fy40qNJc"})[1]
        post_category = category_a.text[2:]

        user_a = post_soup.findAll('a', {"class": "_2tbHP6ZydRpjI44J3syuqC"})   # post__created but user-creator is deleted
        replace_value = ''
        if not user_a:                          # post__created but user-creator is deleted
            replace_value = "doesn't exist"
        else:
            user_a = user_a[0]
            username = user_a.text[2:]
            user_profile_link_new = "https://www.reddit.com" + user_a.attrs["href"]
            user_profile_link_old = "https://old.reddit.com" + user_a.attrs["href"]

            user_page_text_old = get_html(user_profile_link_old)
            page_text_soup = BeautifulSoup(user_page_text_old , features="html.parser")
            karma_spans = page_text_soup.findAll('span', {"class": "karma"})
            if not karma_spans:             # If "You must be 18+ to view this community" is displayed
                replace_value = "private"
            else:
                post_karma = karma_spans[0].text
                comment_karma = karma_spans[1].text

                user_page_text_new = get_html(user_profile_link_new)
                page_text_soup = BeautifulSoup(user_page_text_new, features="html.parser")
                karma_and_cake_spans = page_text_soup.findAll('span', {"class": "_1hNyZSklmcC7R_IfCUcXmZ"})
                user_karma = karma_and_cake_spans[0].text
                user_cake_day = karma_and_cake_spans[1].text

        post_dict['post URL'] = post_url
        post_dict['username'] = "doesn't exist" if not user_a else username
        if replace_value:
            user_karma, user_cake_day, post_karma, comment_karma = [replace_value for i in range(4)]
        post_dict['user karma'] = user_karma
        post_dict['user cake day'] = user_cake_day
        post_dict['post karma'] = post_karma
        post_dict['comment karma'] = comment_karma
        post_dict['post date'] = post_date
        post_dict['number of comments'] = comments_number
        post_dict['number of votes'] = votes_number
        post_dict['post category'] = post_category

        parsed_post_data.append(post_dict)
    except IndexError:
        continue

work_dir_path = os.getcwd()
datetime_now = datetime.datetime.now()
datetime_str = datetime_now.strftime("%Y%m%d%H%M")
file_name = f'reddit-{datetime_str}.txt'
file_path = os.path.join(work_dir_path, file_name)
with open(file_path, 'w') as file:
    for post_dict in parsed_post_data:
        post_data_str = ''
        for data_name in post_dict:
            data_value = post_dict[data_name]
            post_data_str += f'{data_value}; '
        post_data_str = post_data_str[:len(post_data_str)-2]
        file.write(post_data_str + '\n')
