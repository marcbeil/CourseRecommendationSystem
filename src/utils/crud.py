from utils.db_interface import db


def read_topics():
    cursor = db.cursor()
    query = "SELECT * FROM NERD_MODULES_NEW"
    cursor.execute(query)
    rows = cursor.fetchall()

    cursor.close()
    db.close()
    return rows
