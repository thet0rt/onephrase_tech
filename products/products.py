import json
import os
from typing import List
from uuid import UUID, uuid4
import gspread
from gspread import Spreadsheet

import logging
from openpyxl import Workbook

from products.types import ProductData


log = logging.getLogger(os.getenv('APP_NAME'))



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
    
    def get_title(self, title):
        title = title.replace('@new_phrase', self.product_data['phrase_art'])
        return title


    def fill_xlsx_template(self, template: List[list]):
        parent_uuids = {}
        for row in template:
            row[self.column_mapping['tilda_uid']] = self.get_correct_uuid(row[self.column_mapping['tilda_uid']])
            row[self.column_mapping['sku']] = self.product_data['phrase_art']
            row[self.column_mapping['category']] = self.get_category(row[self.column_mapping['category']])
            row[self.column_mapping['title']] = self.get_title(row[self.column_mapping['title']])
            

    def get_template(self):
        products_template = self.worksheet.get("A1:X163")[1:]
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
