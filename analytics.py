import json
import os
from datetime import datetime

import gspread
import retailcrm
from gspread import Spreadsheet
from typing import Optional

import logging
from copy import deepcopy

log = logging.getLogger(os.getenv('APP_NAME'))


class Analytics:

    def __init__(self, start_date: Optional[str], end_date: Optional[str]):
        self.start_date = start_date
        self.end_date = end_date
        self.sh = self.get_spreadsheet()
        self.worksheet = self.sh.worksheet(os.getenv("WORKSHEET_NAME"))
        self.client = retailcrm.v5(
            os.getenv("RETAIL_CRM_URI"), os.getenv("RETAIL_CRM_TOKEN")
        )

    def get_orders_amount_by_creation_date(self) -> int:
        """
        Количество заявок ПО дате заявки
        :return: int
        """
        order_filter = {
            "customFields": {
                "client_type_order": "yurik",
                "new_lead_b2b": True,
            },
            "createdAtFrom": self.start_date,
            "createdAtTo": self.end_date,
        }
        orders = self.client.orders(filters=order_filter, limit=20)
        total_count = orders.get_response().get("pagination", {}).get("totalCount")
        return total_count

    def get_good_orders_amount_by_creation_date(self) -> int:
        """
        Количество качественных заявок ПО дате заявки
        :return:
        """
        order_filter = {
            "customFields": {
                "client_type_order": "yurik",
                "good_lead_b2b": True,
            },
            "createdAtFrom": self.start_date,
            "createdAtTo": self.end_date,
        }
        orders = self.client.orders(filters=order_filter, limit=20)
        total_count = orders.get_response().get("pagination", {}).get("totalCount")
        return total_count

    def get_cold_orders_amount_by_creation_date(self) -> int:
        """
        Количество качественных заявок ПО дате заявки
        :return:
        """
        order_filter = {
            "customFields": {
                "client_type_order": "yurik",
                "cold_lead_b2b": True,
            },
            "createdAtFrom": self.start_date,
            "createdAtTo": self.end_date,
        }
        orders = self.client.orders(filters=order_filter, limit=20)
        total_count = orders.get_response().get("pagination", {}).get("totalCount")
        return total_count

    def make_request(self, page: str, date_type: str):
        order_filter = {
            "customFields": {
                "client_type_order": "yurik",
            }
        }
        if date_type == "real_payment_date":
            order_filter["customFields"].update(
                {"real_date_of_payment": {"min": self.start_date, "max": self.end_date}}
            )
        elif date_type == "creation_date":
            order_filter.update(
                {"createdAtFrom": self.start_date, "createdAtTo": self.end_date}
            )
        response = self.client.orders(filters=order_filter, limit=100, page=page)
        if not response.is_successful():
            raise AnalyticsException(response.get_error_msg())
        return response.get_response().get("orders", []), response.get_response().get(
            "pagination", {}
        ).get("totalPageCount")

    def make_costs_request(self, order_ids: list, page: int = 1):
        costs_filter = {"orderIds": order_ids}
        response = self.client.costs(filters=costs_filter, limit=100, page=page)
        if not response.is_successful:
            raise AnalyticsException(response.get_error_msg())
        return response.get_response().get("costs", []), response.get_response().get(
            "pagination", {}
        ).get("totalPageCount")

    def get_costs_sum_by_real_payment_date(self, date_type: str) -> int:
        """
        Расход по заказам ПО дате оплаты
        :return: int
        """
        orders, total_pages = self.make_request(page=1, date_type=date_type)
        order_list_id = []
        order_list_id.extend([order.get("id") for order in orders])
        current_page = 1
        while current_page < total_pages:
            current_page += 1
            orders, total_pages = self.make_request(current_page, date_type)
            order_list_id.extend([order.get("id") for order in orders])

        total_sum = 0
        current_page = 1
        if order_list_id:
            costs, total_pages = self.make_costs_request(order_list_id)
            while current_page <= total_pages:
                costs, total_pages = self.make_costs_request(order_list_id)
                for cost in costs:
                    total_sum += cost.get("summ", 0)
                current_page += 1
        return total_sum

    def paid_orders_by_payment_date(self, page: int = 1) -> dict:
        order_filter = {
            "customFields": {
                "client_type_order": "yurik",
                "real_date_of_payment": {"min": self.start_date, "max": self.end_date},
            },
            "minPrepaySumm": 1,
        }
        orders = self.client.orders(filters=order_filter, limit=100, page=page)
        if not orders.is_successful():
            raise AnalyticsException(orders.get_error_msg())
        return orders.get_response()

    def get_paid_orders_amount_by_payment_date(self) -> int:
        """
        Количество сделок ПО дате оплаты
        :return:
        """
        orders = self.paid_orders_by_payment_date()
        total_count = orders.get("pagination", {}).get("totalCount")
        return total_count

    def paid_orders_by_creation_date(self, page: int = 1) -> dict:
        order_filter = {
            "customFields": {
                "client_type_order": "yurik",
            },
            "minPrepaySumm": 1,
            "createdAtFrom": self.start_date,
            "createdAtTo": self.end_date,
        }
        orders = self.client.orders(filters=order_filter, limit=100, page=page)
        if not orders.is_successful():
            raise AnalyticsException(orders.get_error_msg())
        return orders.get_response()

    def get_paid_orders_amount_by_creation_date(self):
        """
        Количество сделок ПО дате заявки
        :return:
        """
        orders = self.paid_orders_by_creation_date(page=1)
        total_count = orders.get("pagination", {}).get("totalCount")
        return total_count

    def get_payment_sum_by_payment_date(self):
        """
        Сумма оплат ПО дате оплаты
        :return:
        """
        orders = self.paid_orders_by_payment_date()
        page_amount = orders.get("pagination").get("totalPageCount")
        payment_sum = 0
        for page in range(1, page_amount + 1):
            orders = self.paid_orders_by_payment_date(page)
            order_list = orders.get("orders")
            payment_sum += sum([order.get("prepaySum") for order in order_list])
        return payment_sum

    def get_payment_sum_by_creation_date(self):
        """
        Сумма оплат ПО дате заявки
        :return:
        """
        orders = self.paid_orders_by_creation_date()
        page_amount = orders.get("pagination").get("totalPageCount")
        payment_sum = 0
        for page in range(1, page_amount + 1):
            orders = self.paid_orders_by_creation_date(page)
            order_list = orders.get("orders")
            payment_sum += sum([order.get("prepaySum") for order in order_list])
        return payment_sum

    @staticmethod
    def get_spreadsheet() -> Spreadsheet:
        with open("google_creds.json", "r") as creds_file:
            google_creds = json.load(creds_file)

        gc = gspread.service_account_from_dict(google_creds)
        sh = gc.open_by_key(os.getenv("SPREADSHEET_CODE"))
        return sh

    def create_report(self) -> dict[str, str]:
        response_dict = {
            "orders_amount_by_creation_date": self.get_orders_amount_by_creation_date(),
            "cold_orders_amount_by_creation_date": self.get_cold_orders_amount_by_creation_date(),
            "good_orders_amount_by_creation_date": self.get_good_orders_amount_by_creation_date(),
            "costs_sum_by_real_payment_date": self.get_costs_sum_by_real_payment_date(
                "real_payment_date"
            ),
            "paid_orders_amount_by_payment_date": self.get_paid_orders_amount_by_payment_date(),
            "paid_orders_amount_by_creation_date": self.get_paid_orders_amount_by_creation_date(),
            "payment_sum_by_payment_date": self.get_payment_sum_by_payment_date(),
            "payment_sum_by_creation_date": self.get_payment_sum_by_creation_date(),
        }
        return response_dict

    def create_report_list(self) -> list[str]:
        response_list = [
            self.get_orders_amount_by_creation_date(),
            self.get_cold_orders_amount_by_creation_date(),
            self.get_good_orders_amount_by_creation_date(),
            self.get_paid_orders_amount_by_payment_date(),
            self.get_payment_sum_by_payment_date(),
            self.get_costs_sum_by_real_payment_date("real_payment_date"),
            0,
            self.get_paid_orders_amount_by_creation_date(),
            self.get_payment_sum_by_creation_date(),
            self.get_costs_sum_by_real_payment_date("creation_date"),
            0,
        ]
        return response_list

    @staticmethod
    def transform_date(date: str):
        date_list = date.split(".")
        date_final = f"{date_list[2]}-{date_list[1]}-{date_list[0]}"
        return date_final

    @staticmethod
    def date_after_today(date: str) -> bool:
        try:
            dt_date = datetime.strptime(date, "%d.%m.%Y")
            current_date = datetime.now()
            return dt_date > current_date
        except Exception as exc:
            log.exception(f"Error trying to convert date %s, e = %s", date, exc)

    def update_b2b_data(self):
        for i in list(range(3, 500)):
            date_list = self.worksheet.batch_get([f"B{i}", f"C{i}"])
            date_start, date_end = date_list
            date_start = date_start[0][0]
            date_end = date_end[0][0]
            if self.date_after_today(date_start):
                log.info(
                    f"Finished analytics on dates {date_start} - {date_end}, row {i}"
                )
                return
            self.start_date = self.transform_date(str(date_start))
            self.end_date = self.transform_date(str(date_end))

            response_list = self.create_report_list()
            self.worksheet.update([response_list], f"D{i}")


class AnalyticsB2C:
    def __init__(self, start_date: Optional[str], end_date: Optional[str]):
        self.start_date = start_date
        self.end_date = end_date
        self.sh = self.get_spreadsheet()
        self.worksheet = self.sh.worksheet(os.getenv("WORKSHEET_NAME"))
        self.client = retailcrm.v5(
            os.getenv("RETAIL_CRM_URI"), os.getenv("RETAIL_CRM_TOKEN")
        )
        self.other_chat_methods = ("onlain-pomoshchnik", "wa", "mail", "website-b2b", "telegram-b2b")
        self.all_chat_methods = ("onlain-pomoshchnik", "wa", "mail", "website-b2b",
                                 "telegram-b2b", 'vk', 'inst', 'tg')

    @staticmethod
    def get_spreadsheet() -> Spreadsheet:
        with open("google_creds.json", "r") as creds_file:
            google_creds = json.load(creds_file)

        gc = gspread.service_account_from_dict(google_creds)
        sh = gc.open_by_key(os.getenv("SPREADSHEET_CODE_B2C"))
        return sh

    @staticmethod
    def date_after_today(date: str) -> bool:
        try:
            dt_date = datetime.strptime(date, "%d.%m.%Y")
            current_date = datetime.now()
            return dt_date > current_date
        except Exception as exc:
            log.exception(f"Error trying to convert date %s, e = %s", date, exc)

    @staticmethod
    def transform_date(date: str):
        date_list = date.split(".")
        date_final = f"{date_list[2]}-{date_list[1]}-{date_list[0]}"
        return date_final

    def get_orders_amount_by_social_network(self, social_networks: tuple, new_lead_b2c=False, good_lead_b2c=False,
                                            prepay_sum=False) -> int:
        """
        Количество заявок ПО дате заявки
        :return: int
        """
        order_filter_base = {
            "customFields": {
                "client_type_order": "fizik",
            },
            "createdAtFrom": self.start_date,
            "createdAtTo": self.end_date,
        }
        order_filter: dict = deepcopy(order_filter_base)
        order_filter.update({"orderMethods": social_networks})
        if new_lead_b2c:
            order_filter["customFields"]["new_lead_b2c"] = True
        if good_lead_b2c:
            order_filter["customFields"]["good_lead_b2c"] = True
        if prepay_sum:
            order_filter.update({"minPrepaySumm": 1})
        orders = self.client.orders(filters=order_filter, limit=20)
        if not orders.is_successful():
            log.error(str(orders.get_errors()))
            raise AnalyticsException(orders.get_error_msg())
        total_count = orders.get_response().get("pagination", {}).get("totalCount")
        return total_count

    def paid_orders(self,
                    social_networks: Optional[tuple], by_creation_date=False,
                    by_payment_date=False, page: int = 1):
        order_filter_base = {
            "customFields": {
                "client_type_order": "fizik",
            },
            "minPrepaySumm": 1,
        }
        order_filter: dict = deepcopy(order_filter_base)
        if social_networks:
            order_filter.update({"orderMethods": social_networks})
        if by_creation_date:
            order_filter.update({
                "createdAtFrom": self.start_date,
                "createdAtTo": self.end_date})
        elif by_payment_date:
            order_filter["customFields"]["real_date_of_payment"] = {"min": self.start_date, "max": self.end_date}
        else:
            raise AnalyticsException('Orders must be sorted either by creation_date or payment_date')
        orders = self.client.orders(filters=order_filter, limit=100, page=page)
        if not orders.is_successful():
            log.error(str(orders.get_errors()))
            raise AnalyticsException(orders.get_error_msg())
        return orders.get_response()

    def get_paid_orders_amount(self, social_networks: Optional[tuple], **kwargs) -> int:
        """
        Количество сделок ПО дате оплаты
        :return:
        """
        orders = self.paid_orders(social_networks, **kwargs)
        total_count = orders.get("pagination", {}).get("totalCount")
        return total_count

    def get_payment_sum(self, social_networks: Optional[tuple], **kwargs):
        orders = self.paid_orders(social_networks, **kwargs)
        page_amount = orders.get("pagination").get("totalPageCount")
        payment_sum = 0
        for page in range(1, page_amount + 1):
            orders = self.paid_orders(social_networks, page=page, **kwargs)
            order_list = orders.get("orders")
            payment_sum += sum([order.get("prepaySum") for order in order_list])
        return payment_sum

    def create_report_list(self) -> list[int]:
        response_list = [
            # КОЛ-ВО ЗАЯВОК ПО ДАТЕ ЗАЯВКИ (4 КАНАЛА)
            self.get_orders_amount_by_social_network(self.all_chat_methods, new_lead_b2c=True),
            self.get_orders_amount_by_social_network(("vk",), new_lead_b2c=True),
            self.get_orders_amount_by_social_network(("inst",), new_lead_b2c=True),
            self.get_orders_amount_by_social_network(("tg",), new_lead_b2c=True),
            self.get_orders_amount_by_social_network(self.other_chat_methods, new_lead_b2c=True),
            # КОЛ-ВО КАЧЕСТВЕННЫХ ЗАЯВОК ПО ДАТЕ ЗАЯВКИ (4 КАНАЛА)
            self.get_orders_amount_by_social_network(self.all_chat_methods, good_lead_b2c=True),
            self.get_orders_amount_by_social_network(("vk",), good_lead_b2c=True),
            self.get_orders_amount_by_social_network(("inst",), good_lead_b2c=True),
            self.get_orders_amount_by_social_network(("tg",), good_lead_b2c=True),
            self.get_orders_amount_by_social_network(self.other_chat_methods, good_lead_b2c=True),
            # КОЛ-ВО ЗАКАЗОВ ЧЕРЕЗ МЕССЕНДЖЕРЫ ПО ДАТЕ ОПЛАТЫ (4 КАНАЛА)
            self.get_paid_orders_amount(self.all_chat_methods, by_payment_date=True),
            self.get_paid_orders_amount(("vk",), by_payment_date=True),
            self.get_paid_orders_amount(("inst",), by_payment_date=True),
            self.get_paid_orders_amount(("tg",), by_payment_date=True),
            self.get_paid_orders_amount(self.other_chat_methods, by_payment_date=True),
            # СУММА ОПЛАТ ЧЕРЕЗ МЕССЕНДЖЕРЫ ПО ДАТЕ ОПЛАТЫ (4 КАНАЛА)
            self.get_payment_sum(self.all_chat_methods, by_payment_date=True),
            self.get_payment_sum(("vk",), by_payment_date=True),
            self.get_payment_sum(("inst",), by_payment_date=True),
            self.get_payment_sum(("tg",), by_payment_date=True),
            self.get_payment_sum(self.other_chat_methods, by_payment_date=True),
            # КОЛ-ВО ЗАКАЗОВ ЧЕРЕЗ МЕССЕНДЖЕРЫ ПО ДАТЕ ЗАЯВКИ С ПРЕДОПЛАТОЙ (4 КАНАЛА)
            self.get_paid_orders_amount(self.all_chat_methods, by_creation_date=True),  # here
            self.get_paid_orders_amount(("vk",), by_creation_date=True),
            self.get_paid_orders_amount(("inst",), by_creation_date=True),
            self.get_paid_orders_amount(("tg",), by_creation_date=True),
            self.get_paid_orders_amount(self.other_chat_methods, by_creation_date=True),
            # СУММА ОПЛАТ ЧЕРЕЗ МЕССЕНДЖЕРЫ ПО ДАТЕ ЗАЯВКИ (4 КАНАЛА)
            self.get_payment_sum(self.all_chat_methods, by_creation_date=True),
            self.get_payment_sum(("vk",), by_creation_date=True),
            self.get_payment_sum(("inst",), by_creation_date=True),
            self.get_payment_sum(("tg",), by_creation_date=True),
            self.get_payment_sum(self.other_chat_methods, by_creation_date=True),
            # САЙТ
            self.get_orders_amount_by_social_network(("website",)),
            self.get_paid_orders_amount(("website",), by_payment_date=True),
            self.get_payment_sum(("website",), by_payment_date=True),
            # ОБЩИЕ ДАННЫЕ
            self.get_paid_orders_amount(None, by_payment_date=True),
            self.get_payment_sum(None, by_payment_date=True),
            self.get_paid_orders_amount(None, by_creation_date=True),
            self.get_payment_sum(None, by_creation_date=True),
        ]
        return response_list

    def update_b2c_data(self):
        for i in list(range(3, 500)):
            date_list = self.worksheet.batch_get([f"B{i}", f"C{i}"])
            date_start, date_end = date_list
            date_start = date_start[0][0]
            date_end = date_end[0][0]
            if self.date_after_today(date_start):
                log.info(
                    f"Finished analytics on dates {date_start} - {date_end}, row {i}"
                )
                return
            self.start_date = self.transform_date(str(date_start))
            self.end_date = self.transform_date(str(date_end))
            log.info('start_date=%s, end_date=%s', self.start_date, self.end_date)

            response_list = self.create_report_list()
            self.worksheet.update([response_list], f"D{i}")


class AnalyticsException(Exception):
    pass
