Assignment#3:

Доработать приложение из Assignment#2 таким образом, чтобы сохранение данных вместо выходного файла на диске
осуществлялось в базу данных MongoDB. Количество постов для записи в БД = 1000.
В результирующией базе должно быть не менее двух коллекций.
Использование библиотек ORM для выполнения задания запрещается.

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
8. MongoDB database is installed.
9. Path to ChromeDriver and parameters for connection to MongoDB are specified in the configuration file. For that:
   - create the file named "config.yaml" in the project folder.
   - set up "config.yaml" with the following configuration:
   
   `executable_path: your_path_to_chromedriver`
   
   `database: your_mongo_db_name`
      
   `host: your_host`
   
   `port: your_port`

You can run reddit_parser.py as an autonomous script after having fulfilled all the above.
To start using RESTful service or running unittests located in tests.py, you should run server.py at first.
