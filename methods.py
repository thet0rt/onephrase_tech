import os
from typing import Optional

import retailcrm
import requests

from db import r
from log_settings import log
from datetime import datetime, timedelta
from celery_settings import celery

client = retailcrm.v5(os.getenv("RETAIL_CRM_URI"), os.getenv("RETAIL_CRM_TOKEN"))
ALLOWED_EXTENSIONS = {"zip"}


@celery.task(bind=True)
def handle_webhook_b2c(self, data: dict) -> tuple:
    customer_mail = data.get("email")
    form_id = data.get("formid")
    if customer_exists(self, customer_mail, "email"):
        log.info(f"Customer already exists {customer_mail=}")
        return 200, "Customer already exists"
    response = create_customer(
        personal_data=customer_mail,
        client_type="individual",
        search_type="email",
        form=get_formname(form_id),
    )
    if not response[0]:
        return 400, "Couldnt create a new customer"
    return 200, "Success"


@celery.task(bind=True)
def handle_webhook_b2b(self, data: dict) -> tuple:
    phone_number = data.get("Phone")
    if customer := customer_exists(self, phone_number, "phone"):
        customer_id = customer.get("id")
        log.info(f"Customer already exists {phone_number=}, {customer_id=}")

    else:
        customer = create_customer(
            phone_number, "individual", "phone", "b2b", data.get("Name")
        )
        if not customer[0]:
            return 400, "Couldnt create a new customer"
        customer_id = customer[1].get("id")
    if not customer_id:
        log.error(f"Something is wrong with crm response = {customer[1]}")
        return 400, f"Something is wrong with crm response = {customer[1]}"
    data.update(customer_id=customer_id, client_type="individual")
    return create_b2b_order(data)


def create_customer(
    personal_data: str,
    client_type: str,
    search_type: str,
    form: str,
    name: Optional[str] = None,
) -> tuple:
    if search_type == "email":
        personal_data_wrapped = {"email": personal_data}
    elif search_type == "phone":
        personal_data_wrapped = {"phones": [{"number": personal_data}]}
    else:
        log.error(f"{search_type=} not in ['email', 'phone']")
        return False, f"{search_type=} not in ['email', 'phone']"
    data_to_create = {
        **personal_data_wrapped,
        "firstName": name or "-",
        "contragent": {"contragentType": client_type},
        "customFields": {"feedback_form": form},
    }
    response = client.customer_create(customer=data_to_create, site="new-onephrase-ru")
    if not response.is_successful():
        log.error(
            f"Error while creating customer with {personal_data=}, e={response.get_error_msg()}"
        )
        return False, response.get_response()
    log.info(f"Customer successfully created. {personal_data=}")
    return True, response.get_response()


def customer_exists(self, personal_data: str, search_type: str) -> dict:
    """

    :param self:
    :param personal_data:
    :param search_type: must be in ['email', 'phone']
    :return:
    """
    response = client.customers(filters={search_type: personal_data})
    if not response.is_successful():
        log.error(
            f"Error while making request to find customer in crm = {response.get_error_msg()}"
        )
        raise self.retry(countdown=60)
    customers: list = response.get_response().get("customers")
    return customers[0] if customers else {}


def create_b2b_order(customer_data: dict):
    order = {
        "customer": {"id": customer_data.get("customer_id")},
        "contragent": {"contragent_type": customer_data.get("client_type")},
        "orderMethod": "website-b2b",
        "orderType": "clientb2c",
        "status": "firstcontact",
        "firstName": customer_data.get("Name") or "-",
        "phone": customer_data.get("Phone"),
        "customerComment": customer_data.get("Тираж_и_комментарий_к_заказу"),
        "managerId": 53,
        "customFields": {"client_type_order": "yurik"},
    }
    response = client.order_create(order, site="new-onephrase-ru")
    if not response.is_successful():
        log.error(f"Error while creating new order e={response.get_error_msg()}")
        return 400, f"Error while creating new order e={response.get_error_msg()}"
    order_number = response.get_response().get("order", {}).get("number")
    log.info(f"Created order {order_number}")
    return 200, "Success"


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def get_formname(form_id: str) -> Optional[str]:
    form_mapping = {
        "form666442489": "basement-b2c",
        "form724784561": "pop-up-b2c",
    }
    return form_mapping.get(form_id)


def get_date_from_redis(key: str):
    expire_date = r.get(key)
    if expire_date:
        return datetime.fromisoformat(expire_date.decode("utf-8"))


def humanize_exp_date(exp_date):
    exp_date += timedelta(hours=3)
    return exp_date.strftime("%d %B %Y %H:%M")


def get_session_data(session_id) -> Optional[dict]:
    url = f'https://console.bot-marketing.com/api/public/tunnelSessions/{session_id}'
    try:
        response = requests.get(url)
        response.raise_for_status()
        session_data = response.json()
    except Exception as exc:
        log.exception(exc)
        return
    return session_data


def get_tg_id_by_session_id(session_id):
    session_data = get_session_data(session_id)
    if not session_data:
        return
    tg_id = session_data.get('chat', {}).get('messengerExternalId')
    return tg_id


def check_if_chat_member_by_tg_id(tg_id) -> Optional[bool]:
    url = f'{os.getenv("tg_chat_member_link")}{tg_id}'
    try:
        response = requests.get(url)
        response.raise_for_status()
        tg_data = response.json()
        if not tg_data.get('ok'):
            return
        status = tg_data.get('result', {}).get('status')
        return status in ('member', 'creator')
    except Exception as exc:
        log.exception(exc)
