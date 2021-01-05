Assignment#1:

"Написать Python-скрипт с использованием библиотеки Beautiful Soup по сбору данных с сайта www.reddit.com по постам в категории Top -> This Month . Результат построчно (одна строка = один пост) сложить в текстовый файл с именем reddit-YYYYMMDDHHMM.txt в следующем формате:

UNIQUE_ID;post URL;username;user karma;user cake day;post karma;comment karma;post date;number of comments;number of votes;post category

UNIQUE_ID - буквенно-цифровой уникальный цифровой идентификатор записи длиной 32 символа, формируется при помощи функции uuid1() библиотеки uuid с параметром hex.

Содержимое выходного файла должно формироваться на момент запуска программы за один раз. В имени выходного файла:
YYYY - год, например, 2020
MM - месяц, 12
DD - день
HH - часы
MM - минуты

Выходной файл должен содержать 100 записей заданного формата. В случае, если по причине ограничений reddit.com по конкретному посту не удается собрать данные в нужном формате и полном объеме - пост игнорируется.

Скрипт должен логгировать все значимые события с использованием стандартной библиотеки logging.


Assignment#2:

"Приложение из Assignment#1 изменить таким образом, чтобы данные парсера сохранялись не напрямую в файл, а через отдельный RESTful сервис, доступный на http://localhost:8087/, который в свою очередь предоставляет простой API по работе с базовыми операциями по работе с файлом. Сервис сохраняет результат в текстовый файл с именем reddit-YYYYMMDD.txt

Список методов и endpoits сервиса:

1. GET http://localhost:8087/posts/ возвращает содержимое всего файла в JSON формате
2. GET http://localhost:8087/posts/<UNIQUE_ID>/ возвращает содержимое строки с идентификатором UNIQUE_ID
3. POST http://localhost:8087/posts/ добавляет новую строку в файл, при отсутствии файла - создает новый, проверяет содержимое файла на отсутствие дубликатов по полю UNIQUE_ID перед созданием строки, в случае успеха возвращает код операции 201, а так же JSON формата {""UNIQUE_ID"": номер вставленной строки}
4. DELETE http://localhost:8087/posts/<UNIQUE_ID>/ удаляет строку файла с идентификатором UNIQUE_ID
5. PUT http://localhost:8087/posts/<UNIQUE_ID>/ изменяет содержимое строки файла с идентификатором UNIQUE_ID

Если не указано иное, все запросы возвращают код 200 в случае успеха; те, что ссылаются на номер строки, возвращают 404, если строка с запрашиваемым номером не найдена. Если не указано иное, содержимое ответа пусто. Все непустые ответы - в формате JSON. Все действия, выполняющие запрос - в формате JSON.

Для выполнения задания использовать библиотеку Requests."

_____________________________________________________________________________________________

In order to launch the project locally, make sure the following mandatory steps have been met:
1. You have Python 3.8.5 installed. For that:
    * Install pyenv prerequisites for your OS:
      https://github.com/pyenv/pyenv/wiki/Common-build-problems#prerequisites
    * Install pyenv: `curl https://pyenv.run | bash`
    * Install Python 3.8.5 using pyenv: `pyenv install 3.8.5`
2. `python` command for project folder is overriden:
   `pyenv local 3.8.5`
3. Virtual environment is created. For that:
   `python -m venv venv`
   - then activate the virtual environment:
   `source venv/bin/activate`
4. Packages pip and setuptools are up-to-date:
   `pip install -U pip setuptools`
5. Python dependencies are installed:
   `pip install -r requirements.txt`
6. Google Chrome browser is installed.
7. ChromeDriver from https://sites.google.com/a/chromium.org/chromedriver/home is installed, and its version is the same as Google Chrome version.
8. Path to ChromeDriver is specified in the configuration file. For that:
   - create the file named "config.yaml" in the project folder.
   - set up "config.yaml" with the following configuration:
   `executable_path: your_path_to_chromedriver`

You can run reddit_parser.py as an autonomous script after having fulfilled all the above.

To start using RESTful service, you should run server.py at first. To run unittests located in tests.py, 
in addition to running server, concrete file “test-file.txt” should exist in the project directory. You can pull it from GitHub repository, among others. 
