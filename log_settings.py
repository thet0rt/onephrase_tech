import logging
import os
import sys
from functools import reduce
from typing import Union, Mapping, Iterable, Sequence, Any, Optional
from uuid import uuid4

from pythonjsonlogger import jsonlogger
from flask import request, g

from const import MAX_LOG_SIZE, MAX_CROPPED_LOG_SIZE
from thread_storage import (
    X_REQUEST_ID_HEADER_KEY,
    get_global_log_params,
    get_request_id,
    set_request_id,
)


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Добавление дополнительных полей в запись лога"""

    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)
        log_record[X_REQUEST_ID_HEADER_KEY] = get_request_id()
        log_params = {**get_global_log_params(), **get_context_log_params()}
        for k, v in log_params.items():
            if v:
                log_record[k] = v

    def jsonify_log_record(self, log_record):
        """Из-за ограничений платформы openshift максимальный размер страницы SPI
        ограничен 4096 байт. Обрезаем лог, чтобы не падать при логгировании."""
        log_record_without_crops = {}
        for k, v in log_record.items():
            log_record_without_crops[k] = v
        result_log = super().jsonify_log_record(log_record_without_crops)
        if len(result_log) > MAX_LOG_SIZE:
            for k, v in log_record.items():
                if isinstance(v, (str, bytes)):
                    log_record[k] = crop_log_text(v, log_record.get('level'))
            result_log = super().jsonify_log_record(log_record)
        return result_log


def set_request_id_hook_handler():
    request_id = request.headers.get(X_REQUEST_ID_HEADER_KEY) or str(uuid4())
    set_request_id(request_id)


def log_request(log):
    def inner():
        log.info(
            'Начало запроса %s %s',
            request.method,
            request.path,
            extra={
                'when': 'before',
                'method': request.method,
                'path': request.path,
            }
        )

    return inner


def get_status_from_response(response):
    if 399 < response.status_code < 500:
        d = response.json
        status = get_in(d, ['status'])
        return str(status) if status else None


def get_context_log_params():
    # noinspection PyBroadException
    try:
        return g.setdefault('log_params', {})
    # что бы мы ни делали падать в логах нельзя
    except Exception:
        return {}


def get_in(data: Union[Mapping, Iterable], path: Sequence, default: Any = None) -> Any:
    """Безопасный способ получить данные из вложенных типов
    :param data: данные произвольной вложенности
    :param path: путь до нужного значения
    :param default: возвращаемый параметр по-умолчанию, если значение не нашлось
    """
    try:
        return reduce(lambda d, key: d[key], path, data)
    except (KeyError, IndexError, TypeError):
        return default


def crop_log_text(text: Optional[Union[str, bytes]], level: Optional[str] = None):
    """Обрезать слишком длинный текст ответа, чтобы он помещался в логи
     и попадал в ELK"""
    # noinspection PyBroadException
    try:
        # обрезаю сверху, если ошибка - exception или error
        if text and len(text) > MAX_CROPPED_LOG_SIZE and level in ['EXCEPTION', 'ERROR']:
            text = '<Content was cropped because it\'s size>\n...\n' + str(text[-MAX_CROPPED_LOG_SIZE:])
            return text
        elif text and len(text) > MAX_CROPPED_LOG_SIZE:
            text = str(text[:MAX_CROPPED_LOG_SIZE]) + '\n...\n<Content was cropped because it\'s size>'
    except:
        pass
    return text


def new_logger(name: str, log_level: Union[int, str]) -> logging.Logger:
    log = logging.getLogger(name)
    log_level = logging.getLevelName(log_level)
    log.setLevel(log_level)
    formatter = CustomJsonFormatter(
        '%(name)s %(levelname)s %(module)s %(funcName)s %(message)s',
        rename_fields={
            'levelname': 'level', 'funcName': 'func'
        },
        timestamp='@timestamp'
    )

    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(log_level)
    stdout_handler.setFormatter(formatter)
    file_handler = logging.FileHandler("log/app.log", "a", "utf-8")
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    log.handlers = [stdout_handler, file_handler]

    return log


def add_log_handlers(app, logger):
    """Добавление хендлеров для логгирования запроса"""
    app.before_request(set_request_id_hook_handler)
    app.before_request(log_request(logger))
    app.after_request(log_response(logger))


def log_response(log):

    def inner(response):
        error_status = get_status_from_response(response)
        response_text = getattr(response, 'data', None)
        log.info(
            'Конец запроса %s %s',
            request.method,
            request.path,
            extra={
                'when': 'after',
                'method': request.method,
                'path': request.path,
                'status_code': response.status_code,
                **({'error_status': error_status} if error_status else {}),
                **({'response_text': try_decode(response_text)} if response_text else {}),
            }
        )  # yapf: disable
        return response

    return inner


def try_decode(text):
    try:
        return text.decode('utf-8')
    except:
        pass
    return text


class Logging:
    """
    This is a helper extension, which adjusts logging configuration for the application.
    """

    def __init__(self, app=None):
        if app:
            self.init_app(app)

    def init_app(self, app):
        """
        Common Flask interface to initialize the logging according to the application configuration.
        """
        logger = new_logger(os.getenv('APP_NAME'), os.getenv('LOG_LEVEL'))

        add_log_handlers(app, logger)
