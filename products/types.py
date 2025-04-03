from typing import TypedDict, Dict

class ProductData(TypedDict):
    category_1: str
    category_2: str
    links: Dict[str, str]
    design_number: str
    text: str
