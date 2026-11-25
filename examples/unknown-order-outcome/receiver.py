import sqlite3
from contextlib import closing


def submit(path, reference, key):
    with closing(sqlite3.connect(path)) as db, db:
        db.execute("CREATE TABLE IF NOT EXISTS attempts (reference TEXT, token TEXT)")
        db.execute("CREATE TABLE IF NOT EXISTS orders (reference TEXT, token TEXT UNIQUE)")
        db.execute("INSERT INTO attempts VALUES (?, ?)", (reference, key))
        # NULL is not unique in SQLite: without a key, a second submission
        # really could create a second order, even with the same reference.
        db.execute(
            "INSERT INTO orders VALUES (?, ?) ON CONFLICT(token) DO NOTHING",
            (reference, key),
        )
        first_submission = db.execute("SELECT count(*) FROM attempts").fetchone()[0] == 1

    if first_submission:
        raise TimeoutError("Response lost after receiver commit")
    return "confirmed"


def lookup(path, reference):
    with closing(sqlite3.connect(path)) as db, db:
        db.execute("CREATE TABLE IF NOT EXISTS lookups (reference TEXT)")
        db.execute("INSERT INTO lookups VALUES (?)", (reference,))
    # Model a lagging read view: not finding an order here is not authoritative.
    return "not_found_in_read_view"
