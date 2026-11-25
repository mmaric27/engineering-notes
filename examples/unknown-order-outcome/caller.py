import os
import sqlite3
import sys
from contextlib import closing
from pathlib import Path
from uuid import uuid4

import receiver


def run(directory, contract=None):
    caller_db = directory / "caller.sqlite"
    receiver_db = directory / "receiver.sqlite"
    if contract is not None:
        if contract not in ("keyed", "unkeyed"):
            raise ValueError("Unknown receiver contract")
        reference = str(uuid4())
        key = str(uuid4()) if contract == "keyed" else None
        # Commit the intent and recovery information before any external call.
        with closing(sqlite3.connect(caller_db)) as db, db:
            db.execute("CREATE TABLE intent (reference TEXT, token TEXT, status TEXT)")
            db.execute("INSERT INTO intent VALUES (?, ?, 'unknown')", (reference, key))
    else:
        with closing(sqlite3.connect(caller_db)) as db:
            reference, key, status = db.execute("SELECT * FROM intent").fetchone()
        if status != "unknown":
            return
        if key is None:
            result = receiver.lookup(receiver_db, reference)
            print(result)
            return  # This read view cannot authorize a new submission.

    try:
        status = receiver.submit(receiver_db, reference, key)
    except TimeoutError:
        # Fault injection: stop before the caller can persist any response.
        os._exit(75)

    with closing(sqlite3.connect(caller_db)) as db, db:
        db.execute("UPDATE intent SET status = ? WHERE reference = ?", (status, reference))


if __name__ == "__main__":
    run(Path(sys.argv[1]), *sys.argv[2:])
