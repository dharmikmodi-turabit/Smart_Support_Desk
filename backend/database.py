import pymysql
from fastapi.exceptions import HTTPException


def access_db():
    try:
        connection = pymysql.connect(host='localhost',
                             user='root',
                             password='root',
                             database='smart_support_desk',
                             cursorclass=pymysql.cursors.DictCursor)
        return connection
    except pymysql.MySQLError as e:
        print("DB Connection Error:", e)
        raise HTTPException(status_code=500, detail="Database connection failed")