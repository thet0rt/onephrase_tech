from typing import TypedDict, Dict

class ProductData(TypedDict):
    phrase_art: str
    category_1: str
    category_2: str
    links: Dict[str, str]
    