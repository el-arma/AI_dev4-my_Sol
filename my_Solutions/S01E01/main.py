from dotenv import load_dotenv
import os

load_dotenv()

AI_DEV4_API_KEY = os.getenv("AI_DEV4_API_KEY")

csv_source = f'https://hub.ag3nts.org/data/{AI_DEV4_API_KEY}/people.csv'