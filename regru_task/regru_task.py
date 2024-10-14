# -*- coding: utf-8 -*-
import json
import os
from typing import Optional

import gspread
import requests
import retailcrm
from gspread import Spreadsheet

from mail import send_email
from log_settings import log
from cachetools import TTLCache, cached
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


class CrmMethods:
    client = retailcrm.v5(os.getenv("RETAIL_CRM_URI"), os.getenv("RETAIL_CRM_TOKEN"))

    def __init__(self):
        self.sh = self.get_spreadsheet()
        self.delivery_msg_cfg = self.get_delivery_msg_cfg()

    @staticmethod
    def get_spreadsheet() -> Spreadsheet:
        with open('google_creds.json', 'r') as creds_file:
            google_creds = json.load(creds_file)

        gc = gspread.service_account_from_dict(google_creds)
        sh = gc.open_by_key(os.getenv('SPREADSHEET_CODE'))
        return sh

    def get_delivery_msg_cfg(self) -> dict:
        config = {}
        worksheet = self.sh.worksheet('delivery_msg_cfg')
        ws_data = worksheet.batch_get(['B2:F50'])[0]
        for data in ws_data[1:]:
            days_count = data[2]
            if '-' in days_count:
                days_count = tuple([int(x) for x in days_count.split('-')])
            else:
                days_count = int(days_count)
            config[data[0]] = {'status_msg': data[1],
                               'days_count': days_count,
                               'emoji': data[3],
                               'category': data[4]}
        return config

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

    async def get_orders_by_phone_number(self,
            phone: str, actuality: str
    ) -> Optional[list]:  # todo обработка ошибок. Сделать ретрай
        filters = self.get_status_filters(actuality)
        response = self.client.orders(filters=filters)

        url = f"https://{SUBDOMAIN}.retailcrm.ru/api/v5/orders?filter[customer]={phone}{self.get_status_filters(actuality)}"
        log.debug('url = %s', url)
        headers = {"X-API-KEY": TOKEN}

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                        url, headers=headers, raise_for_status=True
                ) as response:
                    response = await response.json()
                    if not response.get("success") or not response.get("orders"):
                        return
                    return response.get("orders")
            except Exception as e:
                log.error('Error while getting order_info from CRM, exc = %s', e)
                return

    def get_orders_by_phone_number(self, phone: str, actuality: str):
        pass

    def get_status_filters(self, actuality: str) -> str:
        filters = ""
        if actuality == "new":
            for status_code in self.get_message_mapping_config(codes_only=True, categories=('active', 'delivery')):
                filters += f"&filter[extendedStatus][]={status_code}"
        elif actuality == "old":
            for status_code in self.get_message_mapping_config(codes_only=True, categories=('done',)):
                filters += f"&filter[extendedStatus][]={status_code}"
        log.debug('filters= %s', filters)
        return filters

    def get_status_filters_dict(self, actuality: str) -> str:
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

    async def get_orders_by_order_number(self, order_number: str) -> Optional[list]:  # todo обработка ошибок. Сделать ретрай
        # todo сделать небольшой таймаут, чтоб пользователи не ждали долго
        url = f"https://{SUBDOMAIN}.retailcrm.ru/api/v5/orders?filter[numbers][]={order_number}"
        log.debug('url = %s', url)
        headers = {"X-API-KEY": TOKEN}

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                        url, headers=headers, raise_for_status=True
                ) as response:
                    response = await response.json()
                    if not response.get("success") or not response.get("orders"):
                        return
                    return response.get("orders")
            except Exception as e:
                log.error('Error while getting order_info from CRM, exc = %s', e)
                return

