import logging
import psycopg2


class PostgreExecuterError(Exception):
    def __init__(self, thrown_by, text):
        self.thrown_by = thrown_by
        self.text = text


class PostgreQueryCollection:
    create_tables_query = '''                
                    create table if not exists users 	
                    (
                        id            serial       not null
                            constraint users_pkey
                                primary key,
                        username      varchar(100) not null,
                        user_karma    integer      not null,
                        user_cake_day date         not null,
                        post_karma    integer      not null,
                        comment_karma integer      not null
                    );
                    
                    create table if not exists posts
                    (
                        id              serial       not null
                            constraint posts_pkey
                                primary key,
                        unique_id       char(32)     not null
                            constraint posts_unique_id_key
                                unique,
                        post_url        text         not null,
                        post_date       date         not null,
                        comments_number integer      not null,
                        votes_number    integer      not null,
                        post_category   varchar(100) not null,
                        user_id         integer
                            constraint posts_user_id_fkey
                                references users
                                on delete cascade
                    );                
                        '''
    insert_post_query = """
                with ins_user as (
                    insert into users (
                        username, user_karma, user_cake_day, post_karma, comment_karma
                    ) values (%(username)s, %(user_karma)s, %(user_cake_day)s, %(post_karma)s, %(comment_karma)s)
                    returning id
                )
                insert into posts (
                    unique_id, post_url, post_date, comments_number, votes_number, post_category, user_id
                ) values (%(unique_id)s, %(post_url)s, %(post_date)s, %(comments_number)s, %(votes_number)s, 
                        %(post_category)s, (select id from ins_user))
                    """
    get_all_posts_query = '''                
                    select unique_id, post_url, username, user_karma, user_cake_day, post_karma, comment_karma, 
                    post_date, comments_number, votes_number, post_category
                    from users
                    join posts on users.id = posts.user_id 
                        '''
    get_post_query = '''                
                select unique_id, post_url, username, user_karma, user_cake_day, post_karma, comment_karma, 
                post_date, comments_number, votes_number, post_category
                from users
                join posts on users.id = posts.user_id
                where unique_id = %s 
                    '''
    get_all_posts_no_users_query = '''select * from posts'''
    remove_post_query = '''
                with del_post as (
                    delete from posts where unique_id = %s
                    returning user_id
                )
                delete from users where id = (select user_id from del_post); 
                    '''
    update_post_query = """
                with upd_post as (
                    update posts 
                    set post_url = %(post_url)s, 
                        post_date = %(post_date)s, 
                        comments_number = %(comments_number)s, 
                        votes_number = %(votes_number)s, 
                        post_category = %(post_category)s
                    where unique_id = %(unique_id)s
                    returning user_id
                )
                    update users 
                    set username = %(username)s,
                        user_karma = %(user_karma)s, 
                        user_cake_day = %(user_cake_day)s, 
                        post_karma = %(post_karma)s, 
                        comment_karma = %(comment_karma)s
                    where id = (select user_id from upd_post) 
                        """


class PostgreConnector:
    connection_entries = {'database': 'reddit_db',
                          'user': 'postgres',
                          'password': '',
                          'host': '127.0.0.1',
                          'port': '5432'
                          }

    def __init__(self):
        logging.basicConfig(filename="programLogs.log", level=logging.INFO,
                            format='%(asctime)s. %(levelname)s: %(message)s')

    def __enter__(self):
        self.connection = self.connect_to_db()
        self.cursor = self.connection.cursor()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.connection.commit()
        self.connection.close()
        return True

    def connect_to_db(self):
        connection = psycopg2.connect(**self.connection_entries)
        return connection


class PostgreTablesCreator(PostgreConnector):
    def create_tables(self):
        self.cursor.execute(PostgreQueryCollection.create_tables_query)


class PostgreAllPostsInserter(PostgreConnector):
    def __init__(self, post_data):
        super().__init__()
        self.post_data = post_data

    def insert_all_posts_into_db(self):
        for post_dict in self.post_data:
            self.cursor.execute(PostgreQueryCollection.insert_post_query, post_dict)


class PostgreAllPostsGetter(PostgreConnector):
    def get_all_posts_from_db(self):
        try:
            self.cursor.execute(PostgreQueryCollection.get_all_posts_query)
            stored_posts = self.cursor.fetchall()
            return stored_posts
        except psycopg2.errors.UndefinedTable:
            raise PostgreExecuterError(self.__class__.__name__, "Table doesn't exist")


class PostgrePostGetter(PostgreConnector):
    def __init__(self, unique_id):
        super().__init__()
        self.unique_id = (unique_id, )

    def get_post_from_db(self):
        try:
            self.cursor.execute(PostgreQueryCollection.get_post_query, self.unique_id)
            result = self.cursor.fetchall()
            if result:
                stored_post = result[0]
                return stored_post
            return
        except psycopg2.errors.UndefinedTable:
            raise PostgreExecuterError(self.__class__.__name__, "Table doesn't exist")


class PostgrePostRemover(PostgreConnector):
    def __init__(self, unique_id):
        super().__init__()
        self.unique_id = (unique_id, )

    def remove_post_from_db(self):
        try:
            self.cursor.execute(PostgreQueryCollection.remove_post_query, self.unique_id)
            return self.cursor.rowcount
        except psycopg2.errors.UndefinedTable:
            raise PostgreExecuterError(self.__class__.__name__, "Table doesn't exist")


class PostgrePostInserter(PostgrePostGetter):
    def __init__(self, unique_id, post_dict):
        super().__init__(unique_id)
        self.post_dict = post_dict

    def define_stored_post_number(self):
        self.cursor.execute(PostgreQueryCollection.get_all_posts_no_users_query)
        return self.cursor.rowcount

    def insert_post_into_db(self):
        self.cursor.execute(PostgreQueryCollection.insert_post_query, self.post_dict)


class PostgrePostUpdater(PostgrePostGetter):
    def __init__(self, unique_id, post_dict):
        super().__init__(unique_id)
        self.post_dict = post_dict

    def update_post(self):
        self.cursor.execute(PostgreQueryCollection.update_post_query, self.post_dict)