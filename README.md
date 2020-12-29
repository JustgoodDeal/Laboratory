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





In order to launch the project locally, make sure the following mandatory steps have been met:
1. Check whether python 3.8 is installed.
2. The correct versions of the required Python libraries listed in requirements.txt are installed.
3. Google Chrome browser is installed.
4. ChromeDriver from https://sites.google.com/a/chromium.org/chromedriver/home is installed, its version should be the same as Google Chrome version.
5. Perhaps, you will have to specify path to installed ChromeDriver by changing the line in reddit_parser.py:
   use self.driver = webdriver.Chrome(path=”Your path to file”) instead of webdriver.Chrome().

You can run reddit_parser.py as an autonomous script after having fulfilled all the above.

To start using RESTful service, you should run server.py at first. To run unittests located in tests.py, 
in addition to running server, concrete file “test-file.txt” should exist in the project directory. You can pull it from GitHub repository, among others. 
