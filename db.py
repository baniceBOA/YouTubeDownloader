import sqlite3


database = ''
def create_connection(db_file):
    """ create a database connection to the SQLite database
        specified by db_file
    :param db_file: database file
    :return: Connection object or None
    """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Exception as e:
        print(e)

    return conn


def create_table(conn, create_table_sql):
    """ create a table from the create_table_sql statement
    :param conn: Connection object
    :param create_table_sql: a CREATE TABLE statement
    :return:
    """
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except Error as e:
        print(e)


def main():
    database = r"youtube_db.db"
    sql_create_projects_table = '''CREATE TABLE IF NOT EXISTS YouTube (
									id INTEGER NOT NULL, 
									title VARCHAR, 
									thumbnail VARCHAR, 
									path VARCHAR, 
									PRIMARY KEY (id)
									); '''

    

    # create a database connection
    conn = create_connection(database)

    # create tables
    if conn is not None:
        # create projects table
        create_table(conn, sql_create_projects_table)

    else:
        print("Error! cannot create the database connection.")

def insertvalue(conn, title='', thumbnail='', path='.'):
    sql_insert_paramas = ''' INSERT INTO YouTube ( title, thumbnail, path) VALUES (?,?,?)'''
    data_tuple = (title, thumbnail, path)
    try:
        conn.execute(sql_insert_paramas, data_tuple)
        conn.commit()
    except Exception as e:
        print(f'failed with {e}')

def select_all(conn):
    ''' select from the database '''
    try:
        sql_params = '''SELECT * FROM YouTube'''
        cursor = conn.cursor()
        cursor.execute(sql_params)
        rows = cursor.fetchall()
        return rows
    except Exception as e:
        print(f'failed with {e}')
        return []
main()

#insertvalue(conn, 'MoviePie', 'image.png', 'C:\\path')