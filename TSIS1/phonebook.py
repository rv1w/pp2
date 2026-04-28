import json
from connect import get_connection


def create_tables():
    conn = get_connection()
    cur = conn.cursor()

    with open("TSIS1/schema.sql", "r") as f:
        cur.execute(f.read())

    conn.commit()
    cur.close()
    conn.close()


# ----------- HELPERS -----------

def get_or_create_group(cur, group_name):
    cur.execute("SELECT id FROM groups WHERE name=%s", (group_name,))
    row = cur.fetchone()

    if row:
        return row[0]

    cur.execute("INSERT INTO groups(name) VALUES (%s) RETURNING id", (group_name,))
    return cur.fetchone()[0]


def get_contact_id(cur, name):
    cur.execute("SELECT id FROM contacts WHERE name=%s", (name,))
    row = cur.fetchone()
    return row[0] if row else None


# ----------- INSERT -----------

def insert_from_console():
    conn = get_connection()
    cur = conn.cursor()

    name = input("Name: ")
    email = input("Email: ")
    birthday = input("Birthday (YYYY-MM-DD): ")
    group = input("Group: ")

    phone = input("Phone: ")
    phone_type = input("Type (home/work/mobile): ")

    group_id = get_or_create_group(cur, group)

    cur.execute("""
        INSERT INTO contacts(name, email, birthday, group_id)
        VALUES (%s, %s, %s, %s)
        RETURNING id
    """, (name, email, birthday, group_id))

    contact_id = cur.fetchone()[0]

    cur.execute("""
        INSERT INTO phones(contact_id, phone, type)
        VALUES (%s, %s, %s)
    """, (contact_id, phone, phone_type))

    conn.commit()
    cur.close()
    conn.close()


# ----------- QUERY -----------

def query_contacts():
    conn = get_connection()
    cur = conn.cursor()

    print("1 - all")
    print("2 - search name")
    print("3 - search email")
    print("4 - filter by group")
    print("5 - sort")

    choice = input("Choose: ")

    if choice == "1":
        cur.execute("""
            SELECT c.name, c.email, c.birthday, g.name, p.phone, p.type
            FROM contacts c
            LEFT JOIN groups g ON c.group_id = g.id
            LEFT JOIN phones p ON c.id = p.contact_id
        """)

    elif choice == "2":
        name = input("Name: ")
        cur.execute("SELECT * FROM search_contacts(%s)", (name,))

    elif choice == "3":
        email = input("Email: ")
        cur.execute("""
            SELECT * FROM contacts WHERE email ILIKE %s
        """, ('%' + email + '%',))

    elif choice == "4":
        group = input("Group: ")
        cur.execute("""
            SELECT c.name, c.email
            FROM contacts c
            JOIN groups g ON c.group_id = g.id
            WHERE g.name=%s
        """, (group,))

    elif choice == "5":
        sort = input("Sort by (name/birthday): ")
        cur.execute(f"""
            SELECT * FROM contacts ORDER BY {sort}
        """)

    for row in cur.fetchall():
        print(row)

    cur.close()
    conn.close()


# ----------- PAGINATION -----------

def paginate():
    conn = get_connection()
    cur = conn.cursor()

    page = 0
    limit = 5

    while True:
        cur.execute("SELECT * FROM contacts LIMIT %s OFFSET %s", (limit, page * limit))
        rows = cur.fetchall()

        for r in rows:
            print(r)

        action = input("next / prev / quit: ")

        if action == "next":
            page += 1
        elif action == "prev" and page > 0:
            page -= 1
        else:
            break

    cur.close()
    conn.close()


# ----------- JSON -----------

def export_json():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT c.name, c.email, c.birthday, g.name, p.phone, p.type
        FROM contacts c
        LEFT JOIN groups g ON c.group_id = g.id
        LEFT JOIN phones p ON c.id = p.contact_id
    """)

    data = cur.fetchall()

    with open("contacts.json", "w") as f:
        json.dump(data, f, default=str)

    print("Exported to contacts.json")

    cur.close()
    conn.close()


def import_json():
    conn = get_connection()
    cur = conn.cursor()

    with open("contacts.json") as f:
        data = json.load(f)

    for row in data:
        name, email, birthday, group, phone, ptype = row

        cur.execute("SELECT id FROM contacts WHERE name=%s", (name,))
        exists = cur.fetchone()

        if exists:
            choice = input(f"{name} exists. skip/overwrite: ")
            if choice == "skip":
                continue
            else:
                cur.execute("DELETE FROM contacts WHERE name=%s", (name,))

        gid = get_or_create_group(cur, group)

        cur.execute("""
            INSERT INTO contacts(name, email, birthday, group_id)
            VALUES (%s, %s, %s, %s)
            RETURNING id
        """, (name, email, birthday, gid))

        cid = cur.fetchone()[0]

        cur.execute("""
            INSERT INTO phones(contact_id, phone, type)
            VALUES (%s, %s, %s)
        """, (cid, phone, ptype))

    conn.commit()
    cur.close()
    conn.close()


# ----------- MENU -----------

def menu():
    while True:
        print("\n--- PHONEBOOK ---")
        print("1. Add contact")
        print("2. Query")
        print("3. Pagination")
        print("4. Export JSON")
        print("5. Import JSON")
        print("0. Exit")

        choice = input("Select: ")

        if choice == "1":
            insert_from_console()
        elif choice == "2":
            query_contacts()
        elif choice == "3":
            paginate()
        elif choice == "4":
            export_json()
        elif choice == "5":
            import_json()
        elif choice == "0":
            break


if __name__ == "__main__":
    create_tables()
    menu()