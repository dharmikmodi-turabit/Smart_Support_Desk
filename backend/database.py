import pymysql
from fastapi.exceptions import HTTPException

# def get_db():
#     conn = pymysql.connect(
#         host="localhost",
#         user="root",
#         password="root",
#         database="smart_support_desk",
#         cursorclass=pymysql.cursors.DictCursor
#     )
#     try:
#         yield conn
#     finally:
#         conn.close()

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