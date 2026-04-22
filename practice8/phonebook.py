from connect import get_connection

def search(pattern):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM search_contacts(%s)", (pattern,))
    print(cur.fetchall())
    conn.close()

def paginate(limit, offset):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM get_contacts_paginated(%s, %s)", (limit, offset))
    print(cur.fetchall())
    conn.close()

def upsert(name, phone):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("CALL upsert_contact(%s, %s)", (name, phone))
    conn.commit()
    conn.close()

def insert_many():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("CALL insert_many(%s, %s)", (
        ["Ali", "Bob", "BadUser"],
        ["777777", "123123", "abc"]
    ))
    conn.commit()
    conn.close()

def delete(value):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("CALL delete_contact(%s)", (value,))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    upsert("Alik", "777777")
    search("Ali")
    paginate(5, 0)
    insert_many()
    delete("Bob")