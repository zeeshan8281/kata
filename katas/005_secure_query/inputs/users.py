def get_user(db, name):
    """Return (id, name, role) for the user, or None."""
    cur = db.cursor()
    cur.execute("SELECT id, name, role FROM users WHERE name = '%s'" % name)
    return cur.fetchone()


def is_admin(db, name):
    return (get_user(db, name) or (None, None, None))[2] == "admin"
