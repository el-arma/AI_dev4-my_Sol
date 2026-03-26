import base64
from dotenv import load_dotenv
import json
import os
from mcp.server.fastmcp import FastMCP
from mcp_server.mcp_schemas import CalculatorInput, Answer
import requests
from pathlib import Path
from typing import Any, Final


load_dotenv()

AI_DEV4_API_KEY: Final[str] = os.environ["AI_DEV4_API_KEY"]
BASE_URL: Final[str] = os.environ["BASE_URL"]

# mod:
PROJ_BASE_DIR: Final[Path] = Path(__file__)
DATA_BANK_PATH: Final[Path] = PROJ_BASE_DIR / "Data_Bank"
VERIFICATION_ENDPOINT = os.environ["VERIFICATION_ENDPOINT"]
DEFAULT_VERIFY_URL: Final[str] = f"{BASE_URL}/{VERIFICATION_ENDPOINT}"
S01E04_PACKAGE_DOCUMENTATION_URL: Final[str] = os.environ["S01E04_PACKAGE_DOCUMENTATION_URL"]


fastmcp_server = FastMCP()

def _add(x: CalculatorInput) -> float:
    return x.a + x.b

def _multiply(x: CalculatorInput) -> float:
    return x.a * x.b

def _subtract(x: CalculatorInput) -> float:
    return x.a - x.b

def _divide(x: CalculatorInput) -> float:
    return x.a / x.b

def _sum(x: CalculatorInput) -> float:
    return sum(x.operands)

operations_dict = {
    "add": _add,
    "multiply": _multiply,
    "subtract": _subtract,
    "divide": _divide,
    "sum": _sum,
}

@fastmcp_server.tool()
def calculator(input: CalculatorInput) -> float:
    """
    Simple calculator tool for basic arithmetic operations.

    Supported operations:

    - add
        Returns a + b

    - multiply
        Returns a * b

    - subtract
        Returns a - b

    - divide
        Returns a / b

    - sum
        Returns the sum of all values in `operands`

    Input rules:

    - For "add", "multiply", "subtract", "divide":
        Provide:
            a: number
            b: number

    - For "sum":
        Provide:
            operands: list[number]

    Constraints:

    - Do not mix `a`/`b` with `operands`
    - Each operation expects only its required fields
    - Missing or invalid inputs will raise a runtime error

    Notes:

    - Division by zero will raise an error
    - Empty or invalid operand lists will raise an error
    """

    try:
        return operations_dict[input.operation](input)
    except Exception as e:
        raise ValueError(f"Calculation error: {str(e)}")

@fastmcp_server.tool()
def prepare_answer(ans: str) -> Answer:
    """
    Wrap raw declaration text into structured payload.
    """
    return Answer(declaration=ans)

@fastmcp_server.tool()
def fetch_data_from_url(url: str) -> dict:
    """
    Fetch ONLY text content (MD / HTML) from URL.

    INPUT:
        url (str)

    OUTPUT:
    {
        "success": bool,
        "content": str | None,
        "content_type": str | None,
        "error": str | None
    }
    """

    try:
        r = requests.get(url, timeout=10)
        content_type = r.headers.get("Content-Type")

        if not r.ok:
            return {
                "success": False,
                "content": None,
                "content_type": content_type,
                "error": f"HTTP {r.status_code}",
            }

        return {
            "success": True,
            "content": r.text,
            "content_type": content_type,
            "error": None,
        }

    except Exception as e:
        return {
            "success": False,
            "content": None,
            "content_type": None,
            "error": str(e),
        }




########################################################################################





# def _save_json(input) -> None:
#     with input.path.open("w", encoding="utf-8") as f:
#         json.dump(
#             input.data,
#             f,
#             indent=input.indent,
#             ensure_ascii=input.ensure_ascii
#         )


# def _save_txt(input) -> None:
#     if not isinstance(input.data, str):
#         raise TypeError("TXT requires string data")
#     with input.path.open("w", encoding="utf-8") as f:
#         f.write(input.data)


# def _save_image(input) -> None:
#     if not isinstance(input.data, (bytes, bytearray)):
#         raise TypeError("Image formats require bytes data")
#     with input.path.open("wb") as f:
#         f.write(input.data)


# save_handlers = {
#     ".json": _save_json,
#     ".txt": _save_txt,
#     ".png": _save_image,
#     ".jpg": _save_image,
#     ".jpeg": _save_image,
#     ".webp": _save_image,
# }

# @fastmcp_server.tool()
# def save_file(input) -> str:
#     """
#     Universal file saver tool.

#     Supported formats:

#     - .json
#         Save JSON-serializable object

#     - .txt
#         Save plain text

#     - .png / .jpg / .jpeg / .webp
#         Save image from bytes

#     Input:

#     - file_name: str
#     - data: Any
#     - indent: int | None (only for JSON)
#     - ensure_ascii: bool (only for JSON)
#     """

#     path = DATA_BANK_PATH / input.file_name
#     path.parent.mkdir(parents=True, exist_ok=True)

#     suffix = path.suffix.lower()

#     handler = save_handlers.get(suffix)
#     if not handler:
#         raise ValueError(f"Unsupported file format: {suffix}")

#     input.path = path  # inject runtime path
#     handler(input)

#     return str(path)

# def _read_json(input) -> Any:
#     with input.path.open("r", encoding="utf-8") as f:
#         return json.load(f)


# def _read_txt(input) -> str:
#     with input.path.open("r", encoding="utf-8") as f:
#         return f.read()


# def _read_image(input) -> bytes:
#     with input.path.open("rb") as f:
#         return f.read()


# read_handlers = {
#     ".json": _read_json,
#     ".txt": _read_txt,
#     ".png": _read_image,
#     ".jpg": _read_image,
#     ".jpeg": _read_image,
#     ".webp": _read_image,
# }

# @fastmcp_server.tool()
# def read_file(input) -> Any:
#     """
#     Universal file reader tool.

#     Supported formats:

#     - .json
#         Returns parsed JSON object

#     - .txt
#         Returns string content

#     - .png / .jpg / .jpeg / .webp
#         Returns raw bytes

#     Input:

#     - file_name: str
#     """

#     path = DATA_BANK_PATH / input.file_name

#     if not path.exists():
#         raise FileNotFoundError(f"File not found: {path}")

#     suffix = path.suffix.lower()

#     handler = read_handlers.get(suffix)

#     if not handler:
#         raise ValueError(f"Unsupported file format: {suffix}")

#     input.path = path  # inject runtime path

#     return handler(input)