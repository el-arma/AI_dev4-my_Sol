from dotenv import load_dotenv
import os
import pandas as pd
from pathlib import Path
import sqlite3
from typing import Final

load_dotenv()

# Path:
PROJ_BASE_DIR: Final[Path] = Path(os.environ["PROJ_BASE_DIR"])
DATA_BANK_PATH: Final[Path] = PROJ_BASE_DIR / "my_Solutions/Data_Bank"

DB_PATH: Final[Path] = Path(__file__).resolve().parent / "tool_deploy/main.db"

def setup_db(db_path: Path = DB_PATH) -> sqlite3.Connection:
    items = pd.read_csv(DATA_BANK_PATH / "items.csv").rename(columns={"code": "item_code", "name": "item_name"})
    cities = pd.read_csv(DATA_BANK_PATH / "cities.csv").rename(columns={"code": "city_code", "name": "city_name"})
    connections = pd.read_csv(DATA_BANK_PATH / "connections.csv").rename(columns={"itemCode": "item_code", "cityCode": "city_code"})

    stock = (
        connections
        .merge(items, on="item_code")
        .merge(cities, on="city_code")
        [["item_name", "item_code", "city_name", "city_code"]]
        .drop_duplicates()
    )

    conn = sqlite3.connect(db_path)
    stock.to_sql("stock", conn, if_exists="replace", index=False)
    conn.commit()
    print(f"DB ready: {len(stock)} stock rows → {db_path}")
    return conn


if __name__ == "__main__":
    conn = setup_db()
    conn.close()
