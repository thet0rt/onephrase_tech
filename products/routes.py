# -*- coding: utf-8 -*-
import os
from uuid import uuid4

from flask import Response
from flask import render_template
from flask import request, url_for, flash, redirect, jsonify
from flask import send_file, send_from_directory
from flask_smorest import abort

import logging
from . import products_bp

log = logging.getLogger(os.getenv('APP_NAME'))



@products_bp.get("/healthcheck")
def health_check():
    log.info("Healthcheck. Everything is fine. Have a good day!")
    return Response("Healthcheck. Everything is fine. Have a good day!", status=200)

