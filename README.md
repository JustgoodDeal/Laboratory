Assignment#3:

Доработать приложение из Assignment#2 таким образом, чтобы сохранение данных вместо выходного файла на диске
осуществлялось в базу данных. Количество постов для записи в БД = 1000.
Задание сделать для двух вариантов БД: 1) PostgreSQL и 2) MongoDB.
В результирующих базах должно быть не менее двух таблиц и коллекций соответственно.
Использование библиотек ORM для выполнения задания запрещается.

In order to launch the project locally, make sure the following mandatory steps have been met:

1. Check whether python 3.8 is installed.
2. The correct versions of the required Python libraries listed in requirements.txt are installed.
3. Google Chrome browser is installed.
4. ChromeDriver from https://sites.google.com/a/chromium.org/chromedriver/home is installed, its version should be the same as Google Chrome version.
5. Perhaps, you will have to specify path to installed ChromeDriver by changing the line in reddit_parser.py: use self.driver = webdriver.Chrome(path=”Your path to file”) instead of webdriver.Chrome().
6. Check whether you have MongoDB installed.
7. Change the attribute connection_entries in the class MongoExecutor of mongo.py, if you wish to use another host or port to connect to a database instead of specified there.

You can run reddit_parser.py as an autonomous script after having fulfilled all the above.
To start using RESTful service or running unittests located in tests.py, you should run server.py at first.