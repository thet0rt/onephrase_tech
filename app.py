# -*- coding: utf-8 -*-
import os
from uuid import uuid4

from flask import Flask, request, url_for, flash, redirect
from flask import Response
from flask import render_template
from flask import send_file, send_from_directory
from werkzeug.utils import secure_filename

from analytics import Analytics, AnalyticsB2C
from log_settings import log
from methods import handle_webhook_b2c, handle_webhook_b2b, allowed_file, humanize_exp_date, get_date_from_redis
from tasks import sync_analytics, create_links_from_photos, sync_analytics_b2c
from const import UPLOAD_FOLDER

application = Flask(__name__)


@application.route("/download/photo/<filename>", methods=["GET"])
def download_photo(filename):
    path = application.root_path
    path = path + rf"/tg_bot/media/{filename}"
    return send_file(path)


@application.route("/tilda_webhook_b2b", methods=["POST", "GET"])
def webhook_b2b():
    data = request.json
    phone_number = data.get("Phone")
    if not phone_number:
        log.error(f"No phone number in data {data}")
        return Response(status=200)
    handle_webhook_b2b.delay(data=data)
    return Response(status=200)


@application.route("/tilda_webhook_b2c", methods=["POST", "GET"])
def webhook_b2c():
    data = request.json
    customer_mail = data.get("email")
    if not customer_mail:
        log.warning(f"No email in data {data}")
        return Response(status=200)
    handle_webhook_b2c.delay(data=data)
    return Response(status=200)


@application.route("/get_photo/<product>/<phrase>/<color>")
def get_photo(product, phrase, color):
    return send_file(f"./media_compressed/{product}/{phrase}/{color}_compressed.jpg")


@application.route("/get_photo_alternative/<color>/<product>/<phrase>")
def get_photo_alternative(color, product, phrase):
    # return send_file(f"./media_compressed/{color}/{product}/{phrase}_compressed.jpg")
    return send_file(f"./media_compressed/{product}/{phrase}/{color}_compressed.jpg")


@application.route("/get_photo_new/<phrase>")
def get_photo_new(phrase):
    return send_file(f"./media_compressed/other/{phrase}_compressed.jpg")


@application.route("/get_photo_compressed/<folder_name>/<phrase>")
def get_photo_compressed(folder_name, phrase):
    return send_file(f"./media_compressed/{folder_name}/{phrase}.jpg")


@application.route("/upload_photo/", methods=["POST"])
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
    path = application.root_path
    if len(filename) > 70:
        filename = filename[-70:]
    filename_uuid = f"{uuid4()}_{filename}"
    path = path + rf"/tg_bot/media/{filename_uuid}"
    file.save(path)
    link = url_for("download_photo", filename=filename_uuid)
    return Response(link, 200)


@application.get("/analytics")
def get_analytics():
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    if start_date and end_date:
        analytics = Analytics(start_date, end_date)
        return analytics.create_report_list()
    sync_analytics.delay()
    return Response("ok", 200)


@application.get("/analytics_b2c")
def get_analytics_b2c():
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    if start_date and end_date:
        analytics = AnalyticsB2C(start_date, end_date)
        return analytics.create_report_list()
    sync_analytics_b2c.delay()
    return Response("ok", 200)


@application.get("/download_xlsx/<filename>")
def get_links_xlsx(filename):
    path = f"./xlsx_files/{filename}"
    if os.path.exists(path):
        return send_from_directory("./xlsx_files", filename)
    else:
        return "File does not exist", 400


@application.get("/xlsx_info/<filename>")
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


@application.route("/create_links", methods=["GET", "POST"])
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


@application.get("/healthcheck")
def health_check():
    log.info("Healthcheck. Everything is fine. Have a good day!")
    return Response("Healthcheck. Everything is fine. Have a good day!", status=200)


if __name__ == "__main__":
    application.run(host="0.0.0.0", port=8015, debug=True, load_dotenv=True)