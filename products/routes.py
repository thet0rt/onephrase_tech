# -*- coding: utf-8 -*-
import os
from pathlib import Path
from uuid import uuid4

from flask import Response
from flask import render_template
from flask import request, url_for, flash, redirect, jsonify
from flask import send_file, send_from_directory
from flask_smorest import abort

from products.const import PROCESSED_DIR, XLSX_FILES_DIR

from .products import generate_product_xlsx


import logging
from . import products_bp

log = logging.getLogger(os.getenv("APP_NAME"))

import os
from .schemas import ImageRequestSchema


@products_bp.route("/generate", methods=["POST"])
@products_bp.arguments(ImageRequestSchema(many=True))
def generate_images(data):
    generate_product_xlsx.apply_async(args=[data], queue="high_priority")
    return jsonify({"message": "process started"})


@products_bp.get("/healthcheck")
def health_check():
    log.info("Healthcheck. Everything is fine. Have a good day!")
    return Response("Healthcheck. Everything is fine. Have a good day!", status=200)


@products_bp.route("/download_img/<img_name>", methods=["GET"])
def download_img(img_name):
    response = send_file(f"{PROCESSED_DIR}/{img_name}")
    response.direct_passthrough = False
    return response


@products_bp.route("/download_xlsx/<xlsx_filename>", methods=["GET"])
def download_xlsx(xlsx_filename):
    filepath = f"{XLSX_FILES_DIR}/{xlsx_filename}"
    print(os.path.exists(filepath))
    print(filepath)
    response = send_file(
        filepath,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response.direct_passthrough = False
    return response


@products_bp.route("/xlsx_files", methods=["GET"])
def get_xlsx_list():
    xlsx_files_path = Path(XLSX_FILES_DIR)
    files = [f for f in xlsx_files_path.iterdir() if f.is_file() and f.name.endswith('csv')]
    files_sorted = sorted(files, key=lambda f: f.stat().st_ctime, reverse=True)
    return jsonify({"files": [file.name for file in files_sorted]})
