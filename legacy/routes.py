# -*- coding: utf-8 -*-
import os
import re
from uuid import uuid4

from flask import Response
from flask import render_template
from flask import request, url_for, flash, redirect, jsonify
from flask import send_file, send_from_directory
from flask_smorest import abort
from werkzeug.utils import secure_filename

from analytics import Analytics, AnalyticsB2C
import logging
from const import UPLOAD_FOLDER
from db import r
from methods import handle_webhook_b2c, handle_webhook_b2b, allowed_file, humanize_exp_date, get_date_from_redis, \
    get_tg_id_by_session_id, check_if_chat_member_by_tg_id
from regru_task.regru_task import TgIntegration, CrmUpdatesHandler
from tasks import sync_analytics, create_links_from_photos, sync_analytics_b2c
from . import legacy_bp
from .schemas import AddTagSchema

log = logging.getLogger(os.getenv('APP_NAME'))


@legacy_bp.route("/download/photo/<filename>", methods=["GET"])
def download_photo(filename):
    path = legacy_bp.root_path
    path = path + rf"/tg_bot/media/{filename}"
    return send_file(path)


@legacy_bp.route("/tilda_webhook_b2b", methods=["POST", "GET"])
def webhook_b2b():
    data = request.json
    log.info(data)
    phone_number = data.get("Phone")
    if not phone_number:
        log.error(f"No phone number in data {data}")
        return Response(status=200)
    handle_webhook_b2b.delay(data=data)
    return Response(status=200)


@legacy_bp.route("/tilda_webhook_b2c", methods=["POST", "GET"])
def webhook_b2c():
    data = request.json
    log.info(data)
    customer_mail = data.get("email")
    if not customer_mail:
        log.warning(f"No email in data {data}")
        return Response(status=200)
    handle_webhook_b2c.delay(data=data)
    return Response(status=200)


@legacy_bp.route("/get_photo/<product>/<phrase>/<color>")
def get_photo(product, phrase, color):
    return send_file(f"./media_compressed/{product}/{phrase}/{color}_compressed.jpg")


@legacy_bp.route("/get_photo_alternative/<color>/<product>/<phrase>")
def get_photo_alternative(color, product, phrase):
    # return send_file(f"./media_compressed/{color}/{product}/{phrase}_compressed.jpg")
    return send_file(f"./media_compressed/{product}/{phrase}/{color}_compressed.jpg")


@legacy_bp.route("/get_photo_new/<phrase>")
def get_photo_new(phrase):
    return send_file(f"./media_compressed/other/{phrase}_compressed.jpg")


@legacy_bp.route("/get_photo_compressed/<folder_name>/<phrase>")
def get_photo_compressed(folder_name, phrase):
    return send_file(f"./media_compressed/{folder_name}/{phrase}.jpg")


@legacy_bp.route("/upload_photo/", methods=["POST"])
def upload_file():
    # check if the post request has the file part
    if "file" not in request.files:
        return "Error", 400
    file = request.files["file"]
    file_name = request.form["file_name"]
    # If the user does not select a file, the browser submits an
    # empty file without a filename.
    if file_name == "":
        return "Error", 401
    filename = secure_filename(file_name)
    path = legacy_bp.root_path
    if len(filename) > 70:
        filename = filename[-70:]
    filename_uuid = f"{uuid4()}_{filename}"
    path = path + rf"/tg_bot/media/{filename_uuid}"
    file.save(path)
    link = url_for("download_photo", filename=filename_uuid)
    return Response(link, 200)


@legacy_bp.get("/analytics")
def get_analytics():
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    if start_date and end_date:
        analytics = Analytics(start_date, end_date)
        return analytics.create_report_list()
    sync_analytics.delay()
    return Response("ok", 200)


@legacy_bp.get("/analytics_b2c")
def get_analytics_b2c():
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    if start_date and end_date:
        analytics = AnalyticsB2C(start_date, end_date)
        return analytics.create_report_list()
    sync_analytics_b2c.delay()
    return Response("ok", 200)


@legacy_bp.get("/download_xlsx/<filename>")
def get_links_xlsx(filename):
    path = f"./xlsx_files/{filename}"
    if os.path.exists(path):
        return send_from_directory("./xlsx_files", filename)
    else:
        return "File does not exist", 400


@legacy_bp.get("/xlsx_info/<filename>")
def get_info_xlsx(filename):
    path = f"./xlsx_files/{filename}"
    if os.path.exists(path):
        exp_key, ext = os.path.splitext(filename)
        if expiration_date := get_date_from_redis(exp_key):
            expiration_date = humanize_exp_date(expiration_date)
        else:
            expiration_date = "...no time"
        return render_template(
            "links_ready.html", filename=filename, expiration_date=expiration_date
        )
    else:
        return render_template("processing_links.html")


@legacy_bp.route("/create_links", methods=["GET", "POST"])
def upload_files():
    if request.method in ("POST", "PUT"):
        # check if the post request has the file part
        if "file" not in request.files:
            flash("No file part")
            return redirect(request.url)
        file = request.files["file"]
        if file.filename == "":
            flash("No selected file")
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filename_cut, ext = os.path.splitext(filename)
            file_uuid = uuid4()
            file.save(os.path.join(UPLOAD_FOLDER, filename))
            create_links_from_photos.delay(filename, file_uuid)
            xlsx_filename = f"{filename_cut}_{file_uuid}.xlsx"
            download_link = f"/xlsx_info/{xlsx_filename}"
            if request.method == 'POST':
                return redirect(download_link)
    return render_template("create_links.html")


@legacy_bp.get("/healthcheck")
def health_check():
    log.info("Healthcheck. Everything is fine. Have a good day!")
    return Response("Healthcheck. Everything is fine. Have a good day!", status=200)


@legacy_bp.post(f"/{os.getenv('SECRET_PATH')}/<phone_number>")
def get_order_by_phone_number(phone_number):
    session_id = request.form.get('session_id')
    current_numbers = r.smembers(session_id)
    current_numbers = list(current_numbers) if current_numbers else []
    log.info('session_id = %s', session_id)
    phone_pattern = r'^((8|\+7)[\- ]?)?(\(?\d{3}\)?[\- ]?)?[\d\- ]{7,10}$'
    if not re.fullmatch(phone_pattern, phone_number):
        response = {'order_1': 'invalid format'}
        log.info('Wrong phone_number format = %s', phone_number)
        print(f'wrong_phone_number format = {phone_number}')
        return jsonify(response), 400
    if current_numbers and len(current_numbers) >= 3 and phone_number not in current_numbers:
        return Response('Too many requests', 429)
    current_numbers.append(phone_number)
    r.sadd(session_id, *current_numbers, 86400)
    tg_integration = TgIntegration()
    msg = tg_integration.get_actual_orders_msg(phone_number)
    if not msg:
        return Response('Orders not found', 204)
    response = {}
    for i, order in enumerate(msg, 1):
        response.update({f'order_{i}': order})
    return jsonify(response)


@legacy_bp.get(f"/{os.getenv('SECRET_PATH_2')}/<order_number>")
def get_order_by_order_number(order_number):
    if not re.fullmatch(r'[0-9]{1,5}[ACАСаaсc]', order_number):
        response = {'order_1': 'invalid format'}
        return jsonify(response), 400
    tg_integration = TgIntegration()
    msg = tg_integration.get_order_by_order_number_msg(order_number.upper())
    if not msg:
        return Response('Orders not found', 204)
    response = {}
    for i, order in enumerate(msg, 1):
        response.update({f'order_{i}': order})
    return jsonify(response)


@legacy_bp.get('is_tg_member/<session_id>')
def check_tg_member(session_id):
    tg_id = get_tg_id_by_session_id(session_id)
    if not tg_id:
        abort(404, message='tg_id not found God knows why')
    is_chat_member = check_if_chat_member_by_tg_id(tg_id)
    return jsonify({'is_member': is_chat_member})


@legacy_bp.post('add_tag')
@legacy_bp.arguments(AddTagSchema, location='form')
def add_tag_to_customer(arguments: dict):
    from regru_task.regru_task import CrmMethods
    crm_client = CrmMethods()
    response = crm_client.edit_customer(arguments['customer_id'], delete=False, tag=arguments['tag'])
    return jsonify({'response': response})
