# -*- coding: utf-8 -*-
import os
from uuid import uuid4

from flask import Response
from flask import render_template
from flask import request, url_for, flash, redirect, jsonify
from flask import send_file, send_from_directory
from flask_smorest import abort

from .products import generate_product_xlsx


import logging
from . import products_bp

log = logging.getLogger(os.getenv('APP_NAME'))

import os
from .schemas import ImageRequestSchema


@products_bp.route("/generate", methods=["POST"])
@products_bp.arguments(ImageRequestSchema)
def generate_images(data):
    generate_product_xlsx.delay(data)
    return jsonify({"message": "process started", "results": links})

# # Раздача файлов (для тестирования)
# @products_bp.route("/output/<filename>")
# def get_generated_image(filename):
#     return send_from_directory(UPLOAD_FOLDER, filename)


@products_bp.get("/healthcheck")
def health_check():
    log.info("Healthcheck. Everything is fine. Have a good day!")
    return Response("Healthcheck. Everything is fine. Have a good day!", status=200)


@products_bp.route("/download_img/<img_name>", methods=["GET"])
def download_img(img_name):
    return send_file(f"products/processed_images/{img_name}")
