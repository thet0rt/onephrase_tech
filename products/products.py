import json
import os
from typing import List
from uuid import UUID, uuid4
import gspread
from gspread import Spreadsheet

import logging
from openpyxl import Workbook
from PIL import Image, ImageDraw, ImageFont
from werkzeug.utils import secure_filename
from transliterate import translit


from products.types import ProductData

log = logging.getLogger(os.getenv('APP_NAME'))

STATIC_DIR = "static"
UNPROCESSED_DIR = 'products/initial_images'
PROCESSED_DIR = "./processed_images"
os.makedirs(PROCESSED_DIR, exist_ok=True)


class Products:

    column_mapping = {
        'tilda_uid': 0,
        'sku': 1,  # phrase
        'category': 2,
        'title': 3,
        'description': 4,  # useless
        'text': 5,  # useless
        'photo': 6,  # link
        'price': 7,  # useless
        'quantity': 8,  # useless
        'price_old': 9,  # useless
        'editions': 10,  # useless
        'external_id': 11,  # useless
        'parent_uid': 12,
        'categories': 13,
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
        if name == 'random':
            return uuid4()
        elif str(name).startswith('tilda_uid'):
            parent_uid = self.parent_uids.get(name)
            if not parent_uid:
                self.parent_uids[name] = parent_uid
            return parent_uid
        return ''
    
    def get_category(self, category: str) -> str:
        if category:
            category = category.replace('@category_1', f'{self.product_data["category_1"]};')
            category = category.replace('@category_2', f'{self.product_data["category_2"]};')
        return category
    
    def get_title(self, title: str):
        title = title.replace('@new_phrase', self.product_data['phrase_art'])
        return title
    
    def get_link(self, photo: str):
        link = self.product_data['links'].get(photo)
        if not link:
            log.warning(f'No link found for product: {photo}')
        return link
                    


    def fill_xlsx_template(self, template: List[list]):
        parent_uuids = {}
        for row in template:
            row[self.column_mapping['tilda_uid']] = self.get_correct_uuid(row[self.column_mapping['tilda_uid']])
            row[self.column_mapping['sku']] = self.product_data['phrase_art']
            row[self.column_mapping['category']] = self.get_category(row[self.column_mapping['category']])
            row[self.column_mapping['title']] = self.get_title(row[self.column_mapping['title']])
            row[self.column_mapping['photo']] = self.get_link(row[self.column_mapping['photo']])
            row[self.column_mapping['parent_uid']] = self.get_correct_uuid(row[self.column_mapping['parent_uid']])
            row[self.column_mapping['categories']] = self.get_category(row[self.column_mapping['categories']])


    def get_template(self):
        products_template = self.worksheet.get("A1:X163")[1:]
        self.fill_xlsx_template(products_template)
        # print(products_template)
        # Создаём новую Excel-книгу
        wb = Workbook()
        ws = wb.active
        ws.title = "Таблица"

        # Записываем данные в Excel
        for row in products_template:
            print(row)
            ws.append(row)

        #todo изменить значения некоторых ячеек в каждом ряду.

        # Сохраняем в файл
        wb.save("table.xlsx")

        print("Данные сохранены в table.xlsx")
        # self.worksheet.update([response_list], f"D{i}")



def generate_images(data) -> ProductData:
    results = []
    links = {}
    product_data: ProductData = {}
    for item in data["items"]:
        product = item["product"].split('.')[0]
        text = item["text"]
        x, y = item["coordinates"]["x"], item["coordinates"]["y"]
        font_size = item["fontSize"]

        folder_path = f'{UNPROCESSED_DIR}/{product}'
        objects = os.listdir(folder_path)
        files = [obj for obj in objects if os.path.isfile(os.path.join(folder_path, obj))]

        for file in files:
            input_path = f'products/initial_images/{product}/{file}'

            color = file.split('.')[0]
            phrase = translit(text, "ru", True)
            filename = f"{product}_{color}_{phrase}_{uuid4()}.png"
            filename = secure_filename(filename)
            output_path = os.path.join(PROCESSED_DIR, filename)

            if not os.path.exists(input_path):
                log.error(f"Файл {product} не найден")
            
            image = Image.open(input_path)
            draw = ImageDraw.Draw(image)

            try:
                font = ImageFont.truetype("products/assets/AvantGardeC_regular.otf", font_size)
            except IOError as exc:
                log.error(exc)
                font = ImageFont.load_default()

            # Добавляем текст
            draw.text((x, y), text, fill="white", font=font)

            # Сохраняем изображение
            image.save(output_path)
            link_name = f'{product}_{color}'
            link = f'{os.getenv("SERVICE_URL")}/products/download_img/{filename}'  # todo create endpoint for downloading this
            links[link_name] = link
            results.append({"product": product, "output": output_path})
    product_data = dict(
        phrase_art=text,
        category_1=data['category_1'],
        category_2=data['category_2'],
        links=links
    )