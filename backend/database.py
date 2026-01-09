import pymysql

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
    connection = pymysql.connect(host='localhost',
                             user='root',
                             password='root',
                             database='smart_support_desk',
                             cursorclass=pymysql.cursors.DictCursor)
    return connection