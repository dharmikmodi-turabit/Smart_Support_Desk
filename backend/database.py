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
    except Exception as e:
        raise HTTPException(
        status_code=500,
        detail=str(e)
    )