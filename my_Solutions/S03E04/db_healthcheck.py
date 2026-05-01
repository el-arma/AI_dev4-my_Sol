import sqlite3
from pathlib import Path
from typing import Final

DB_PATH: Final[Path] = Path(__file__).resolve().parent / "tool_deploy/main.db"


def check_db(db_path: Path = DB_PATH) -> None:
    if not db_path.exists():
        print(f"FAIL: DB not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    # Check table exists
    tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    table_names = [t["name"] for t in tables]
    print(f"Tables: {table_names}")
    assert "stock" in table_names, "FAIL: 'stock' table missing"

    # Check row count
    count = conn.execute("SELECT COUNT(*) FROM stock").fetchone()[0]
    print(f"Row count: {count}")
    assert count > 0, "FAIL: stock table is empty"

    # Check columns
    cols = [row[1] for row in conn.execute("PRAGMA table_info(stock)").fetchall()]
    print(f"Columns: {cols}")
    for expected in ("item_name", "item_code", "city_name", "city_code"):
        assert expected in cols, f"FAIL: missing column '{expected}'"

    # Sample rows
    rows = conn.execute("SELECT * FROM stock LIMIT 5").fetchall()
    print("\nSample rows:")
    for row in rows:
        print(dict(row))

    # Unique index sanity: no duplicate (item_code, city_code) pairs
    dupes = conn.execute("""
        SELECT item_code, city_code, COUNT(*) AS cnt
        FROM stock
        GROUP BY item_code, city_code
        HAVING cnt > 1
    """).fetchall()
    assert len(dupes) == 0, f"FAIL: {len(dupes)} duplicate (item_code, city_code) pairs found"

    conn.close()
    print("\nAll checks passed.")


if __name__ == "__main__":
    check_db()
