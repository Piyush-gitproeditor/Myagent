import sqlite3, hashlib
from config import DB_PATH

def conn():
    c = sqlite3.connect(DB_PATH)
    c.execute("""CREATE TABLE IF NOT EXISTS opps(
        id TEXT PRIMARY KEY, source TEXT, title TEXT, url TEXT,
        deadline TEXT, kind TEXT, score REAL, reason TEXT,
        status TEXT DEFAULT 'new')""")
    return c

def make_id(source, url):
    return hashlib.md5(f"{source}:{url}".encode()).hexdigest()

def save_new(c, o):
    """Returns True only if the opportunity was not already in the DB."""
    oid = make_id(o.get("source", ""), o.get("url", ""))
    cur = c.execute(
        "INSERT OR IGNORE INTO opps(id,source,title,url,deadline,kind,score,reason) "
        "VALUES(?,?,?,?,?,?,?,?)",
        (oid, o.get("source"), o.get("title"), o.get("url"),
         o.get("deadline"), o.get("kind"), o.get("score"), o.get("reason")))
    c.commit()
    return cur.rowcount == 1