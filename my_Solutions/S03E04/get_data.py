from dotenv import load_dotenv
import os
from pathlib import Path
import requests
from typing import Final

load_dotenv()

# url:
BASE_URL_DATA_SOURCE: Final = os.environ["S03E04_DATA_SOURCE"]

# Paths:
PROJ_BASE_DIR: Final[Path] = Path(os.environ["PROJ_BASE_DIR"])
DATA_BANK_PATH: Final[Path] = PROJ_BASE_DIR / "my_Solutions/Data_Bank/S03E04_data"

# Create directory if it doesn't exist
DATA_BANK_PATH.mkdir(parents=True, exist_ok=True)

csv_files_to_get = ["cities.csv", "items.csv", "connections.csv"]

for csv_file in csv_files_to_get:

    full_url = f"{BASE_URL_DATA_SOURCE}/{csv_file}"

    full_output_path: Path = DATA_BANK_PATH / csv_file

    with requests.get(full_url, stream=True) as r:
        
        r.raise_for_status()

        with open(full_output_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    
    print(f"{csv_file} downloaded!")

print("All csv downloaded!")