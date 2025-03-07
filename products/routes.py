# -*- coding: utf-8 -*-
import os
from uuid import uuid4

from flask import Response
from flask import render_template
from flask import request, url_for, flash, redirect, jsonify
from flask import send_file, send_from_directory
from flask_smorest import abort
from werkzeug.utils import secure_filename
from transliterate import translit
from .products import Products


import logging
from . import products_bp

log = logging.getLogger(os.getenv('APP_NAME'))

from PIL import Image, ImageDraw, ImageFont
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
    results = []
    links = {}

    for item in data["items"]:
        product = item["product"].split('.')[0]
        text = item["text"]
        x, y = item["coordinates"]["x"], item["coordinates"]["y"]
        font_size = item["fontSize"]

        folder_path = f'{UNPROCESSED_DIR}/{product}'
        objects = os.listdir(folder_path)
        files = [obj for obj in objects if os.path.isfile(os.path.join(folder_path, obj))]

        for file in files:
            print(file)
            input_path = f'products/initial_images/{product}/{file}'

            color = file.split('.')[0]
            phrase = translit(text, "ru", True)
            filename = f"{product}_{color}_{phrase}_{uuid4()}.png"
            filename = secure_filename(filename)
            output_path = os.path.join(PROCESSED_DIR, filename)
            print(input_path)

            if not os.path.exists(input_path):
                return jsonify({"error": f"Файл {product} не найден"}), 404
            
            image = Image.open(input_path)
            draw = ImageDraw.Draw(image)

            try:
                font = ImageFont.truetype("products/assets/AvantGardeC_regular.otf", font_size)
            except IOError as exc:
                log.error(exc)
                font = ImageFont.load_default()

            # Добавляем текст
            draw.text((x, y), text, fill="white", font=font)

            # Сохраняем изображение
            image.save(output_path)
            link_name = f'{product}_{color}'
            link = f'{os.getenv("SERVICE_URL")}/products/download_img/{filename}'  # todo create endpoint for downloading this
            print(link)
            print(link_name)
            links[link_name] = link
            results.append({"product": product, "output": output_path})
    print(links)
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
