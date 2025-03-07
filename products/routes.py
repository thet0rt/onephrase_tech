# -*- coding: utf-8 -*-
import os
from uuid import uuid4

from flask import Response
from flask import render_template
from flask import request, url_for, flash, redirect, jsonify
from flask import send_file, send_from_directory
from flask_smorest import abort

from .products import Products


import logging
from . import products_bp

log = logging.getLogger(os.getenv('APP_NAME'))

import os
from .schemas import ImageRequestSchema


# Директории
STATIC_DIR = "static"
UNPROCESSED_DIR = 'products/initial_images'
PROCESSED_DIR = "./processed_images"
os.makedirs(PROCESSED_DIR, exist_ok=True)



@products_bp.route("/generate", methods=["POST"])
@products_bp.arguments(ImageRequestSchema)
def generate_images(data):

    return jsonify({"message": "Images generated", "results": links})

# # Раздача файлов (для тестирования)
# @products_bp.route("/output/<filename>")
# def get_generated_image(filename):
#     return send_from_directory(UPLOAD_FOLDER, filename)


@products_bp.get("/healthcheck")
def health_check():
    log.info("Healthcheck. Everything is fine. Have a good day!")
    return Response("Healthcheck. Everything is fine. Have a good day!", status=200)

@products_bp.route("/test", methods=["GET"])
def test():
    config = Products()
    template = config.get_template()
    return Response()
