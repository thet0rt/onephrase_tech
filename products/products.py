from copy import deepcopy
from datetime import datetime as dt
import json
import logging
import os
from typing import List
from uuid import UUID, uuid4
import csv
import base64
import io

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
            category_1 = category_1 + '; ' if self.product_data["category_2"] else category_1
            category = category.replace(
                "@category_1", f'{category_1}'
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
        text_image_white = item.get("text_image_white")
        text_image_black = item.get("text_image_black")

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
            if (product, color) in BLACK_COLOR_ITEMS:
                text_image_base64 = text_image_black
            else:
                text_image_base64 = text_image_white

            if text_image_base64:
                try:
                    header, encoded = text_image_base64.split(",", 1)
                    decoded = base64.b64decode(encoded)
                    text_overlay = Image.open(io.BytesIO(decoded)).convert("RGBA")

                    # Уменьшаем изображение в 2 раза
                    new_size = (text_overlay.width // 2, text_overlay.height // 2)
                    text_overlay = text_overlay.resize(new_size, Image.Resampling.LANCZOS)
                    image.paste(text_overlay, (x-30, y-30), text_overlay)
                    text_overlay.save('./test.png')
                except Exception as e:
                    log.error(f"Ошибка при наложении текстового изображения: {e}")
            image.save(output_path, "JPEG", quality=85, optimize=True)
            link_name = f"{product}_{color}"
            link = f'{os.getenv("SERVICE_URL")}/api/products/download_img/{filename}'
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
        # print(row)
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
    header = rows[0]

    with open(filepath, mode="w", newline='', encoding="utf-8") as file:
        writer = csv.writer(file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        for row in rows:
            row += [""] * (len(header) - len(row))
            # print(len(row))
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

#
# import cairo
# import gi
# gi.require_version('Pango', '1.0')
# gi.require_version('PangoCairo', '1.0')
# from gi.repository import Pango, PangoCairo
#
# import os
#
# def draw_text_with_cairo(
#     text: str,
#     font_path: str,
#     font_size: int = 32,
#     line_height: float = 1.0,
#     letter_spacing: int = 0,
#     text_color: str = "#FFFFFF",
#     bg_color: str = "#000000",
#     output_path: str = "output.png",
#     surface_width: int = 500,
#     surface_height: int = 200
# ):
#     # Проверяем что шрифт существует
#     if not os.path.exists(font_path):
#         raise FileNotFoundError(f"Font file not found: {font_path}")
#
#     # Создаем поверхность
#     surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, surface_width, surface_height)
#     ctx = cairo.Context(surface)
#
#     # Фон
#     bg_r, bg_g, bg_b = hex_to_rgb(bg_color)
#     ctx.set_source_rgb(bg_r, bg_g, bg_b)
#     ctx.paint()
#
#     # Создаем Pango контекст
#     layout = PangoCairo.create_layout(ctx)
#
#     # Настройка шрифта через FontDescription
#     font_desc = Pango.FontDescription()
#     font_name = load_font_to_system(font_path)
#     font_desc.set_family(font_name)
#     font_desc.set_absolute_size(font_size * Pango.SCALE)
#     layout.set_font_description(font_desc)
#
#     # Настройка текста
#     layout.set_text(text, -1)
#
#     # Letter-spacing
#     attrs = Pango.AttrList()
#     if letter_spacing:
#         attr = Pango.attr_letter_spacing_new(letter_spacing * Pango.SCALE)  # Pango масштабирует
#         attrs.insert(attr)
#     layout.set_attributes(attrs)
#
#     # Line-spacing (Pango не очень удобно поддерживает line_height напрямую)
#     # Можно частично управлять вручную через разбивку текста
#
#     # Цвет текста
#     text_r, text_g, text_b = hex_to_rgb(text_color)
#     ctx.set_source_rgb(text_r, text_g, text_b)
#
#     # Позиция (пока фиксированная, можно тоже параметризовать)
#     x, y = 50, 50
#     ctx.move_to(x, y)
#
#     # Рендер
#     PangoCairo.show_layout(ctx, layout)
#
#     # Сохраняем
#     surface.write_to_png(output_path)
#
# def load_font_to_system(font_path: str) -> str:
#     """
#     Регистрация шрифта во временной Fontconfig конфигурации.
#     WARNING: Pango по-простому НЕ умеет грузить TTF напрямую, ему нужно имя шрифта.
#     Поэтому тут предполагаем, что у тебя название файла примерно совпадает с font-family.
#     """
#     font_name = os.path.splitext(os.path.basename(font_path))[0]
#     return font_name
#
# def hex_to_rgb(hex_color: str):
#     """Преобразование HEX в нормализованные значения RGB"""
#     hex_color = hex_color.lstrip('#')
#     lv = len(hex_color)
#     return tuple(int(hex_color[i:i + lv // 3], 16) / 255.0 for i in range(0, lv, lv // 3))