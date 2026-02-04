import pymysql
from fastapi.exceptions import HTTPException


def access_db():
    """
    Establish and return a connection to the MySQL database.

    This function connects to the `smart_support_desk` MySQL database
    using PyMySQL and returns a connection object with dictionary-style
    cursors, allowing results to be accessed as dictionaries.

    Returns:
    - pymysql.connections.Connection: Database connection object.

    Raises:
    - RuntimeError: If the connection to the database fails.
    """

    try:
        connection = pymysql.connect(host='localhost',
                             user='root',
                             password='root',
                             database='smart_support_desk',
                             cursorclass=pymysql.cursors.DictCursor)
        return connection
    except pymysql.MySQLError as e:
        raise RuntimeError(f"Database connection failed: {e}")