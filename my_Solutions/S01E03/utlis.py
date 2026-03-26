import re

def find_my_flag(text: str):
    
    match = re.search(r"\{FLG:.*?\}", text)

    if match:
        return match.group()
