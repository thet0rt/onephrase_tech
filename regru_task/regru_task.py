# -*- coding: utf-8 -*-
import json
import os
from datetime import datetime as dt
from datetime import timedelta
from typing import Optional

import gspread
import requests
import retailcrm
from cachetools import TTLCache, cached
from gspread import Spreadsheet

from log_settings import log
from mail import send_email
from regru_task.exceptions import *


class CrmUpdatesHandler:
    @staticmethod
    def get_payment_date(order_data):

        payment_dict = order_data.get('order', {}).get('payments')
        payment_datetime = None
        for payment in payment_dict.values():
            if len(payment_dict.values()) > 1:
                if payment.get('type') in ['robokassa', 'oplata-na-saite', 'b2bpay', 'cloudpayments-onephrase']:
                    payment_datetime = payment.get('paidAt')
                    break
            else:
                payment_datetime = payment.get('paidAt')
        return payment_datetime[:10] if payment_datetime else None

    @classmethod
    def update_payment_date(cls, order_data, order_id):
        payment_datetime = cls.get_payment_date(order_data)
        if not payment_datetime:
            PaymentStatusError(f'Не удалось получить payment_date по заказу {order_id}')
        order = {
            'id': order_id,
            'customFields': {'real_date_of_payment': payment_datetime}
        }
        site = order_data.get('order').get('site')
        CrmMethods.edit_result(order, site)

    @classmethod
    def update_real_payment_date(cls, order_id):
        log.info(f'Обновляю payment_status заказа {order_id}')
        order_data = CrmMethods.get_order_data_retailcrm(order_id)
        if not order_data:
            return
        try:
            order_number = order_data.get('order', {}).get('number')
            cls.update_payment_date(order_data, order_id)
            log.info('Successfully updated payment_date - %s', order_number)
        except Exception as exc:
            error = f'Error while changing payment date/adding position - order_id {order_id} - error {exc}'
            log.error(error)
            send_email('ERROR', error)

    @staticmethod
    def get_since_id():
        with open(f'regru_task/since_id.txt', 'r', encoding='utf-8') as file:
            for line in file:
                since_id = int(line)
                return since_id

    @staticmethod
    def set_since_id(since_id):
        with open(f'regru_task/since_id.txt', 'w', encoding='utf-8') as file:
            file.write(str(since_id))
            log.info(f'Новый sinceId = {since_id}')

    @classmethod
    def update_status(cls):
        log.info('Запустилась таска new_website')
        while True:
            since_id = cls.get_since_id()
            changes_list = CrmMethods.get_changes_list(since_id)
            if not changes_list:
                break
            for record in changes_list:
                external_id = (record.get('order', {})).get('externalId')
                field = record.get('field')
                new_value = record.get('newValue')
                if isinstance(new_value, dict):
                    code = new_value.get('code') if field in ['payments.status', 'status'] else None
                    order_id = record.get('order', {}).get('id')
                    if all([field == 'payments.status', not external_id,
                            code == 'paid']):  # обновляет поле real_payment_date
                        cls.update_real_payment_date(order_id)
                    if field == 'status' and code == 'website-order':
                        order_data = CrmMethods.get_order_data_retailcrm(order_id)
                        if order_data.get('order', {}).get('delivery', {}).get('integrationCode') == 'rs_simple_pochta':
                            order_number = order_data.get('order', {}).get('number')
                            ext_order_id = order_data.get('order', {}).get('externalId')
                            RusPostMethods.integrate_ruspost(ext_order_id, order_number)

                if field == 'integration_delivery_data.track_number' and isinstance(new_value, str):
                    order_id = record.get('order', {}).get('id')
                    order_data = CrmMethods.get_order_data_retailcrm(order_id)
                    if order_data.get('order', {}).get('delivery', {}).get('integrationCode') == 'cdek-1532':
                        order_number = order_data.get('order').get('number')
                        cdek_number = record.get('newValue')
                        CdekMethods.add_order_id_to_cdek(order_number, cdek_number)
            cls.set_since_id(changes_list[-1]['id'])


class CdekMethods:
    cdek_client_id = os.getenv('cdek_client_id')
    cdek_client_secret = os.getenv('cdek_client_secret')

    @classmethod
    @cached(TTLCache(maxsize=1, ttl=3600))
    def get_cdek_token(cls):
        url = 'https://api.cdek.ru/v2/oauth/token?parameters'
        client_id = cls.cdek_client_id
        client_secret = cls.cdek_client_secret
        response = requests.post(
            url,
            data={"grant_type": "client_credentials"},
            auth=(client_id, client_secret),
        )
        return response.json()["access_token"]

    @classmethod
    def add_order_id_to_cdek(cls, order_id, cdek_number):
        url = 'https://api.cdek.ru/v2/orders'
        headers = {
            "accept": "application/json",
            "Authorization": f'Bearer {cls.get_cdek_token()}',
            "content-type": "application/json"
        }
        order = {
            'cdek_number': cdek_number,
            'sender': {
                'company': f'onephrase.ru - номер заказа {order_id}'
            }
        }
        print(order)
        try:
            response = requests.patch(url=url, json=order, headers=headers)
            print(response.json())
            response.raise_for_status()
            log.info(f'Успешно изменил заказ {order_id} - {response.status_code})')
        except Exception as exc:
            log.error(f'CDEK - не удалось обновить заказ(( {order_id} - {exc}')
            send_email('ERROR', f'CDEK - не удалось обновить заказ(( {order_id} - {exc}')

    @classmethod
    def get_cdek_order_info(cls, cdek_uuid) -> Optional[dict]:
        url = f"https://api.cdek.ru/v2/orders/{cdek_uuid}"
        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {cls.get_cdek_token()}",
            "content-type": "application/json",
        }

        try:
            response = requests.get(url=url, headers=headers)
            response.raise_for_status()
            log.debug(response.json())
            return response.json()
        except Exception as exc:
            log.error(f'CDEK - Error while getting order info for cdek_uuid={cdek_uuid} - {exc}')
            send_email('CDEK ERROR', f'CDEK - Error while getting order info for cdek_uuid={cdek_uuid} - {exc}')

    @classmethod
    def get_cdek_status(cls, cdek_uuid) -> dict:
        cdek_status = {"status": None, "planned_date": None}
        order_info = cls.get_cdek_order_info(cdek_uuid)
        log.debug(order_info)
        status_list = order_info.get("entity", {}).get("statuses")
        if status_list:
            cdek_status.update(status=status_list[0].get("name"))
        cdek_status.update(
            planned_date=order_info.get("entity", {}).get("planned_delivery_date")
        )
        return cdek_status


class RusPostMethods:
    ruspost_token = os.getenv('ruspost_token')
    ruspost_key = os.getenv('ruspost_key')

    @classmethod
    def get_ruspost_parcel(cls, ext_order_id):
        url = f'https://otpravka-api.pochta.ru/1.0/backlog/search?query={ext_order_id}'

        request_headers = {
            "Content-Type": "application/json",
            "Accept": "application/json;charset=UTF-8",
            "Authorization": "AccessToken " + cls.ruspost_token,
            "X-User-Authorization": "Basic " + cls.ruspost_key
        }

        response = requests.get(url, headers=request_headers)
        response.raise_for_status()
        search_result = response.json()
        if len(search_result) > 1:
            raise RusPostIntegrationException('Found more than one parcel')
        if len(search_result) < 1:
            raise RusPostIntegrationException('No parcel has been found')
        return search_result[0]

    @classmethod
    def change_ruspost_parcel(cls, parcel, order_id):
        url = f'https://otpravka-api.pochta.ru/1.0/backlog/{parcel.get("id")}'
        data = {
            'order-num': order_id
        }
        parcel.update(data)

        request_headers = {
            "Content-Type": "application/json",
            "Accept": "application/json;charset=UTF-8",
            "Authorization": "AccessToken " + cls.ruspost_token,
            "X-User-Authorization": "Basic " + cls.ruspost_key
        }
        try:
            response = requests.put(url, headers=request_headers, json=parcel)
        except Exception as exc:
            log.error('Exception while changing parcel in RusPost e=%s', exc)
            raise exc
        response.raise_for_status()
        log.info(f'order_id={order_id} was successfully changed in RusPost')

    @classmethod
    def integrate_ruspost(cls, ext_order_id, order_id):
        try:
            parcel = cls.get_ruspost_parcel(ext_order_id)
            track_number = parcel.get('barcode')
            CrmMethods.add_ruspost_track_to_crm(ext_order_id, track_number)
            cls.change_ruspost_parcel(parcel, order_id=order_id)
        except Exception as exc:
            log.error(f'Error while integrating RusPost exc={exc}')

    @classmethod
    def get_ruspost_order_info(cls, ext_order_id) -> dict:
        url = f'https://www.pochta.ru/api/tracking/api/v1/trackings/by-barcodes?language=ru' \
              f'&track-numbers={ext_order_id}'

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json;charset=UTF-8",
            "Authorization": "AccessToken " + cls.ruspost_token,
            "X-User-Authorization": "Basic " + cls.ruspost_key
        }
        try:
            response = requests.get(url=url, headers=headers)
            response.raise_for_status()
            log.debug('Ruspost response = %s', response.json())

            return response.json()
        except Exception as exc:
            log.error('Error while making ruspost request exc=%s', exc)


class CrmMethods:
    client = retailcrm.v5(os.getenv("RETAIL_CRM_URI"), os.getenv("RETAIL_CRM_TOKEN"))

    @classmethod
    def add_ruspost_track_to_crm(cls, ext_order_id: str, track_number: str):
        order = {
            'externalId': ext_order_id,
            'delivery': {
                'data': {
                    'trackNumber': track_number
                }
            }
        }
        edit_result = cls.client.order_edit(order=order, uid_type='externalId', site='new-onephrase-ru')
        if not edit_result.is_successful():
            raise RetailCrmIntegrationError('Error while adding ruspost trackNumber to CRM')
        log.info('Ruspost trackNumber has been successfully added to CRM')

    @classmethod
    def edit_result(cls, order: dict, site: str) -> None:

        edit_result = cls.client.order_edit(order=order, uid_type='id', site=site)
        if not edit_result.is_successful():
            raise PaymentStatusError(f'не удалось поменять заказ {order.get("id")}')
        log.info(f'Успешно проставил реальную дату оплаты для заказа {order.get("id")}')

    @classmethod
    def get_order_data_retailcrm(cls, order_id, site='new-onephrase-ru'):
        response = cls.client.order(uid=order_id, uid_type='id', site=site)
        return response.get_response()

    @classmethod
    def change_order_status(cls, order_id, new_status: str):
        """
        @param order_id:
        @param new_status: delay-new, product-booking-new
        """
        order = {
            'id': order_id,
            'status': new_status
        }
        edit_result = cls.client.order_edit(order=order, uid_type='id')
        if edit_result.is_successful():
            log.info(f'Изменил статус заказа {order_id} на {new_status} - {edit_result.get_status_code()}')
        else:
            log.error(
                f'Не удалось поменять статус заказа {order_id} на {new_status} - {edit_result.get_status_code()} -'
                f' {edit_result.get_response()}')
            send_email('ERROR',
                       f'Не удалось поменять статус заказа {order_id} на {new_status} -'
                       f' {edit_result.get_status_code()} - {edit_result.get_response()}')

    @classmethod
    def check_stocks_info(cls, stock_item_id: int, quantity: int) -> bool:
        result = cls.client.inventories(filters={'ids': [stock_item_id],
                                                 'sites': ['new-onephrase-ru']})
        if not result.is_successful():
            raise StocksError(f'Error while sending inventories request - {result.get_status_code()}')
        offer = result.get_response().get('offers')
        if not offer:
            raise StocksError(f'Item with id {stock_item_id} not found')
        quantity_instock = offer[0].get('quantity')
        return quantity_instock >= quantity

    @classmethod
    def track_number_to_crm(cls, order_id, track_number):
        order = {
            'externalId': order_id,
            'delivery': {"data": {'trackNumber': track_number},
                         "code": 'sdek-v-2'
                         }
        }
        edit_result = cls.client.order_edit(order=order, uid_type='externalId')
        log.info(f'Результат изменения заказа {order_id} - {edit_result.get_status_code()}')
        if edit_result.get_status_code() == 400:
            raise CDEK_Error('не удалось поменять заказ в crm')

    @classmethod
    def get_changes_list(cls, since_id):
        log.debug(f'Делаю запрос в crm с since_id {since_id}')
        result = cls.client.orders_history(filters={'sinceId': since_id}, limit=100)
        changes_list = (result.get_response()).get('history')
        if not changes_list:
            log.debug(f'Нет изменений. sinceId = {since_id}')
        return changes_list

    @classmethod
    def get_orders_by_phone_number(cls, phone: str, filters: dict) -> Optional[list]:
        order_filters = {
            'customer': phone
        }
        order_filters.update(filters)
        response = cls.client.orders(filters=order_filters)
        if response.is_successful():
            return response.get_response()['orders']
        log.error(response.get_error_msg())

    @classmethod
    def get_orders_by_order_number(cls, order_number: str) -> Optional[list]:
        filters = {
            'numbers': [order_number]
        }
        response = cls.client.orders(filters=filters)
        if response.is_successful():
            return response.get_response()['orders']
        log.error(response.get_error_msg())


class TgIntegration:

    def __init__(self):
        self.sh = self.get_spreadsheet()
        self.delivery_msg_cfg = self.get_delivery_msg_cfg()

    @staticmethod
    def get_spreadsheet() -> Spreadsheet:
        with open('google_creds.json', 'r') as creds_file:
            google_creds = json.load(creds_file)

        gc = gspread.service_account_from_dict(google_creds)
        sh = gc.open_by_key(os.getenv('SPREADSHEET_CODE_TG'))
        return sh

    def get_delivery_msg_cfg(self) -> dict:
        config = {}
        worksheet = self.sh.worksheet('delivery_msg_cfg')
        ws_data = worksheet.batch_get(['B2:I50'])[0]
        for data in ws_data[1:]:
            status = data[0]
            condition = data[1]
            condition_days = data[2]
            days_count = data[3]
            category = data[4]
            if '-' in days_count:
                days_count = tuple([int(x) for x in days_count.split('-')])
            else:
                days_count = int(days_count)
            status_cfg = {'status_msg': data[6],
                          'days_count': days_count,
                          'emoji': data[5],
                          'category': category,
                          'count_logic': data[7]}
            if condition:
                config[status] = dict(condition=status_cfg,
                                      condition_days=condition_days,
                                      category=category)
                status_cfg.update({condition: condition_days})
            else:
                config[status] = status_cfg
        return config

    def get_actual_orders_msg(self, phone_number: str) -> Optional[list]:
        filters = self.get_status_filters_dict('new')
        orders = CrmMethods.get_orders_by_phone_number(phone_number, filters)
        if orders:
            orders_info = self.process_order_data(orders)
            return orders_info

    def get_order_by_order_number_msg(self, order_number: str):
        order_number = self.normalize_order_number(order_number)
        orders = CrmMethods.get_orders_by_order_number(order_number)
        if orders:
            if orders_info := self.process_order_data(orders):
                return orders_info

    @staticmethod
    def normalize_order_number(order_number: str) -> str:
        order_number = order_number.replace('А', 'A')
        order_number = order_number.replace('С', 'C')
        return order_number

    def get_status_filters_dict(self, actuality: str) -> dict:
        '''
        Example
        order_filter = {
        "customFields": {
        "client_type_order": "yurik",
        "real_date_of_payment": {"min": self.start_date, "max": self.end_date},
            },
        "minPrepaySumm": 1,
        }
        '''
        status_codes = []
        filters = {'extendedStatus': status_codes}
        if actuality == "new":
            for status_code in self.get_message_mapping_config(codes_only=True, categories=('active', 'delivery')):
                status_codes.append(status_code)
        elif actuality == "old":
            for status_code in self.get_message_mapping_config(codes_only=True, categories=('done',)):
                status_codes.append(status_code)
        log.debug('filters= %s', filters)
        return filters

    def get_message_mapping_config(self,
                                   codes_only: bool = False, categories: tuple = ()
                                   ) -> dict:
        codes = {key for key, val in self.delivery_msg_cfg.items() if val.get('category') in categories}
        return codes if codes_only else self.delivery_msg_cfg

    def process_order_data(self, order_data: list) -> list[str]:
        info_list = []
        config = self.get_message_mapping_config()
        for order in order_data:
            number = order.get("number")
            status = order.get("status")
            items = order.get("items")
            if not items:
                continue
            current_config = config.get(status, {})
            if current_config.get('condition'):
                condition = self.check_condition(order, current_config)
                current_config = current_config.get(condition, {})
            emoji = current_config.get("emoji", "")
            order_number_msg = f"{emoji} Заказ №{number}"
            item_msg = self.get_item_list(items)
            if not item_msg:
                continue
            status_msg = current_config.get("status_msg")
            if not status_msg:
                log.warning("No status msg for order %s, %s", number, order)
                status_msg = ''
            delivery_status_msg = self.get_delivery_status_msg(order, current_config)
            if not order_number_msg:
                log.error("No order_number_msg for order %s, %s", number, order)
                continue
            message = (
                f"{order_number_msg}\n{status_msg}\n{item_msg}"
            )
            if delivery_status_msg:
                message += f'\n\n{delivery_status_msg}'
            info_list.append(message)
        return info_list

    @staticmethod
    def get_item_list(items: list) -> str:
        items_description = "\nСостав заказа:"
        for count, item in enumerate(items, 1):
            name = item.get("offer", {}).get("displayName")
            quantity = item.get("quantity")
            if not name or not quantity:
                log.error(f'Error with item description item = {item}')
                return ''
            items_description += f"\n{count}. {name} - {quantity} шт."
        return items_description

    def get_delivery_status_msg(self, order: dict, current_config) -> str:
        category = current_config['category']
        count_logic = current_config['count_logic']
        days_count = current_config.get('days_count')
        if not count_logic:
            return ''
        if category == 'active':
            return self.get_dispatch_msg_new(order, count_logic, days_count)
        elif category == 'delivery':
            self.get_delivery_message(order)

    def get_delivery_message(self, order):
        delivery_type = order.get("delivery", {}).get("code")
        if delivery_type == "sdek-v-2":
            delivery_msg = self.get_cdek_msg(order)
            return delivery_msg
        elif delivery_type == 'pochta-rossii-treking-tarifikator':
            delivery_msg = self.get_ruspost_msg(order)
            return delivery_msg
        elif delivery_type == 'self-delivery':
            return ''
        else:
            log.warning("Delivery type not in [sdek-v-2, pochta-rossii-treking-tarifikator,"
                        " self-delivery, self-delivery] order=%s",
                        order.get('number'))
            return ''

    @staticmethod
    def get_cdek_msg(order: dict) -> Optional[str]:
        cdek_uuid = order.get("delivery", {}).get("data", {}).get("externalId")
        track_number = order.get("delivery", {}).get("data", {}).get("trackNumber")
        cdek_status = CdekMethods.get_cdek_status(cdek_uuid)
        delivery_status = cdek_status.get("status")
        planned_date = cdek_status.get("planned_date")
        if not delivery_status or not planned_date:
            log.error('Something is wrong with cdek_status = %s', cdek_status)
            return ""
        delivery_msg = (f"\nТип доставки: СДЭК"
                        f"\nТрек-номер для отслеживания: {track_number}"
                        f"\nСтатус доставки: {delivery_status}"
                        f"\nОриентировочная дата прибытия: {planned_date}")
        return delivery_msg

    def get_ruspost_msg(self, order: dict) -> Optional[str]:
        ruspost_tracking_number = order.get("delivery", {}).get("data", {}).get("trackNumber")
        ruspost_status = self.get_ruspost_status(ruspost_tracking_number)
        delivery_status = ruspost_status.get("status")
        planned_date = ruspost_status.get("planned_date")
        if not delivery_status:
            log.error('Something is wrong with ruspost = %s', ruspost_status)
            return ""
        delivery_msg = (f"\nТип доставки: Почта России"
                        f"\nТрек-номер для отслеживания: {ruspost_tracking_number}"
                        f"\nСтатус доставки: {delivery_status}")
        if planned_date:
            delivery_msg += f"\nОриентировочная дата прибытия: {planned_date}"

        return delivery_msg

    @staticmethod
    def get_ruspost_status(ruspost_tracking_number) -> dict:
        ruspost_status = {"status": None, "planned_date": None}
        log.debug('ruspost_tracking_number = %s', ruspost_tracking_number)
        order_info = RusPostMethods.get_ruspost_order_info(ruspost_tracking_number)
        try:
            status_info = order_info.get('detailedTrackings', {})[0].get('trackingItem')
            status = status_info.get('commonStatus')
            expected_delivery_date = status_info.get('shipmentTripInfo', {}).get('expectedDeliveryDate')
            if expected_delivery_date:
                expected_delivery_date = expected_delivery_date[:10]
                log.debug('Expected_delivery_date = %s', expected_delivery_date)
                ruspost_status.update(
                    status=status,
                    planned_date=expected_delivery_date
                )
            log.debug('ruspost_status=%s', ruspost_status)
        except (TypeError, IndexError, AttributeError) as e:
            log.error('Error while getting ruspost stastus, exc = %s', e)
        return ruspost_status

    @staticmethod
    def get_dispatch_msg_new(order: dict, count_logic: str, days_count: tuple) -> str:
        '''
        real_date_of_payment + days_count
        '''
        if count_logic == 'real_date_of_payment':
            real_date_of_payment = order.get('customFields', {}).get('real_date_of_payment')
            if not real_date_of_payment:
                log.error("Something is wrong with real_date_of_payment order= %s", order.get('number'))
                return ''
            start_date = dt.strptime(real_date_of_payment, '%Y-%m-%d')
        elif count_logic == 'current_date':
            start_date = dt.now()
        else:
            log.error('Count logic not found in config')
            return ''

        sending_date_1 = start_date + timedelta(days=days_count[0])
        sending_date_2 = start_date + timedelta(days=days_count[1])
        sending_date_1 = sending_date_1.strftime("%d.%m.%Y")
        sending_date_2 = sending_date_2.strftime("%d.%m.%Y")
        return f"Ориентировочная дата отправки {sending_date_1} - {sending_date_2}"

    @staticmethod
    def check_condition(order: dict, current_config: dict):
        condition_days = current_config.get('condition_days')
        real_date_of_payment = order.get('customFields', {}).get('real_date_of_payment')
        if not real_date_of_payment:
            log.error("Something is wrong with real_date_of_payment order= %s", order.get('number'))
            return ''
        if not isinstance(condition_days, int):
            log.error("Something is wrong with condition_days (config) order= %s")
            return ''
        real_date_of_payment = dt.strptime(real_date_of_payment, '%Y-%m-%d')
        today = dt.now()
        days_since = (today - real_date_of_payment).days
        if days_since <= condition_days:
            return 'days_less_n'
        return 'days_more_n'
