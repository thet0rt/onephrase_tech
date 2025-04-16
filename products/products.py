from copy import deepcopy
from datetime import datetime as dt
import json
import logging
import os
from typing import List
from uuid import UUID, uuid4
import csv

import gspread
from gspread import Spreadsheet
from openpyxl import Workbook
from PIL import Image, ImageDraw, ImageFont
from transliterate import translit
from werkzeug.utils import secure_filename

from celery_settings import celery
from products.const import PROCESSED_DIR, UNPROCESSED_DIR, XLSX_FILES_DIR
from products.types import ProductData
import pytz

log = logging.getLogger(os.getenv("APP_NAME"))
os.makedirs(PROCESSED_DIR, exist_ok=True)
os.makedirs(XLSX_FILES_DIR, exist_ok=True)
BLACK_COLOR_ITEMS = [('hoodie', 'milk'),
                     ('sweatshirt', 'milk'),
                     ('longsleeve', 'milk'),
                     ('tshirt-basic', 'milk'),
                     ('tshirt-trueover', 'coldwhite'),
                     ('tshirt-trueover100', 'coldwhite'),
                     ('hoodie', 'melange'),
                     ('tshirt-basic', 'melange')]


class Products:
    column_mapping = {
        "tilda_uid": 0,
        "sku": 1,  # design_number
        "category": 2,
        "title": 3,
        "description": 4,  # useless
        "text": 5,  # useless
        "photo": 6,  # link
        "price": 7,  # useless
        "quantity": 8,  # useless
        "price_old": 9,  # useless
        "editions": 10,  # useless
        "external_id": 11,  # useless
        "parent_uid": 12,
        "categories": 13,
    }

    def __init__(self, product_data: ProductData):
        self.sh = self.get_spreadsheet()
        self.worksheet = self.sh.worksheet(os.getenv("WORKSHEET_NAME_PRODUCTS"))
        self.product_data = product_data
        self.parent_uids = {}

    @staticmethod
    def get_spreadsheet() -> Spreadsheet:
        with open("google_creds.json", "r") as creds_file:
            google_creds = json.load(creds_file)

        gc = gspread.service_account_from_dict(google_creds)
        sh = gc.open_by_key(os.getenv("SPREADSHEET_CODE_PRODUCTS"))
        return sh

    def get_correct_uuid(self, name) -> UUID:
        if name == "random":
            return str(uuid4())
        elif str(name).startswith("tilda_uid"):
            parent_uid = self.parent_uids.get(name)
            if not parent_uid:
                parent_uid = str(uuid4())
                self.parent_uids[name] = parent_uid
            return parent_uid
        return ""

    def get_category(self, category: str) -> str:
        if category:
            category_1 = self.product_data["category_1"]
            category_1 = category_1 + '; ' if category_1 else category_1
            category = category.replace(
                "@category_1", f'{self.product_data["category_1"]}'
            )
            category = category.replace(
                "@category_2", f'{self.product_data["category_2"]}'
            )
            category = category.strip()
        return category

    def get_title(self, title: str):
        text = self.product_data["text"]
        while '\n' in text:
            text = text.replace('\n', ' ')
        title = title.replace("@new_phrase", text)
        return title

    def get_link(self, photo: str):
        link = self.product_data["links"].get(photo)
        if not link:
            log.warning(f"No link found for product: {photo}")
        return link

    def fill_xlsx_template(self, template: List[list]):
        parent_uuids = {}
        for row in template:
            row[self.column_mapping["tilda_uid"]] = self.get_correct_uuid(
                row[self.column_mapping["tilda_uid"]]
            )
            row[self.column_mapping["sku"]] = self.product_data["design_number"]
            row[self.column_mapping["category"]] = self.get_category(
                row[self.column_mapping["category"]]
            )
            row[self.column_mapping["title"]] = self.get_title(
                row[self.column_mapping["title"]]
            )
            row[self.column_mapping["photo"]] = self.get_link(
                row[self.column_mapping["photo"]]
            )
            row[self.column_mapping["parent_uid"]] = self.get_correct_uuid(
                row[self.column_mapping["parent_uid"]]
            )
            row[self.column_mapping["categories"]] = self.get_category(
                row[self.column_mapping["categories"]]
            )

    def generate_xlsx(self, index: int):
        products_template = self.worksheet.get("A1:X163")
        titles = products_template[:1]
        rows = products_template[1:]

        self.fill_xlsx_template(rows)
        if index == 0:
            rows = titles + rows
        return rows



def generate_images(data: dict) -> ProductData:
    results = []
    links = {}
    text = data["text"]
    for item in data["items"]:
        product = item["product"].split(".")[0]
        x, y = item["coordinates"]["x"], item["coordinates"]["y"]
        font_size = item["fontSize"]

        folder_path = f"{UNPROCESSED_DIR}/{product}"
        objects = os.listdir(folder_path)
        files = [
            obj for obj in objects if os.path.isfile(os.path.join(folder_path, obj))
        ]

        for file in files:
            if not file.endswith(".jpg"):
                continue
            input_path = f"products/initial_images/{product}/{file}"

            color = file.split(".")[0]
            phrase = translit(text, "ru", True)
            filename = f"{product}_{color}_{phrase}_{uuid4()}.jpg"
            filename = secure_filename(filename)
            output_path = os.path.join(PROCESSED_DIR, filename)

            if not os.path.exists(input_path):
                log.error(f"Файл {product} не найден")

            image = Image.open(input_path)
            draw = ImageDraw.Draw(image)

            try:
                font = ImageFont.truetype(
                    "products/assets/AvantGardeC_regular.otf", font_size*6
                )
            except IOError as exc:
                log.error(exc)
                font = ImageFont.load_default()

            if (product, color) in BLACK_COLOR_ITEMS:
                text_color = '#222222'
            else:
                text_color = 'white'

            draw.text((x*6, y*6), text, fill=text_color, font=font)

            width, height = image.size
            new_width = int(width * 0.5)
            new_height = int(height * 0.5)
            image = image.resize((new_width, new_height))
            image.save(output_path, "JPEG", quality=85, optimize=True)
            link_name = f"{product}_{color}"
            link = f'{os.getenv("SERVICE_URL")}/api/products/download_img/{filename}'  # todo create endpoint for downloading this
            links[link_name] = link
            results.append({"product": product, "output": output_path})
    product_data = dict(
        text=text,
        category_1=data["category_1"],
        category_2=data["category_2"],
        links=links,
        design_number=data["design_number"],
    )
    return product_data

def generate_xlsx(rows):
    wb = Workbook()
    ws = wb.active
    ws.title = "Таблица"
    for row in rows:
        print(row)
        ws.append(row)

    moscow_tz = pytz.timezone("Europe/Moscow")
    current_time = dt.now(moscow_tz).strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"table_{current_time}.csv"
    wb.save(f"{XLSX_FILES_DIR}/{filename}")
    log.info(f"Данные сохранены в {filename}")


def generate_csv(rows):
    moscow_tz = pytz.timezone("Europe/Moscow")
    current_time = dt.now(moscow_tz).strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"table_{current_time}.csv"
    filepath = os.path.join(XLSX_FILES_DIR, filename)

    with open(filepath, mode="w", newline='', encoding="utf-8-sig") as file:
        writer = csv.writer(file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        for row in rows:
            writer.writerow(row)

    print(f"CSV файл сохранён в {filename}")


def add_additional_products(data):
    product_list = data['items']
    tshirt_trueover = next((item for item in product_list if item.get('product') == 'tshirt-trueover.png'), None)
    trueover_100 = deepcopy(tshirt_trueover)
    trueover_100['product'] = 'tshirt-trueover100'
    product_list.append(trueover_100)


@celery.task()
def generate_product_xlsx(items):
    rows = []
    for i, data in enumerate(items):
        add_additional_products(data)
        product_data = generate_images(data)
        product = Products(product_data)
        new_rows = product.generate_xlsx(i)
        rows = rows + new_rows
    generate_csv(rows)
    log.info("Products file generated sucessfully")
    return 200, "Products file generated sucessfully"
