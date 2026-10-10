#!/usr/bin/env python3
"""Minimal Ch10 connection, cursor, and result example."""
from contextlib import closing

from course_db import connect


with closing(connect()) as conn:
    with closing(conn.cursor()) as cur:
        cur.execute("SELECT DATABASE(), CURRENT_USER(), @@autocommit")
        print(cur.fetchone())
