import threading
from contextlib import contextmanager

X_REQUEST_ID_KEY = 'x_request_id'
X_REQUEST_ID_HEADER_KEY = 'X-Request-ID'
storage = threading.local()


def set_request_id(request_id):
    setattr(storage, X_REQUEST_ID_KEY, request_id)


def get_request_id():
    return getattr(storage, X_REQUEST_ID_KEY, None)


@contextmanager
def set_global_log_params(**kwargs):
    """Установка глобальных параметров логгирования. Для предотвращения
    потенциальных коллизий использовать только в качестве контекстного
    менеджера"""
    old_log_params = getattr(storage, 'log_params', {})
    storage.log_params = {**old_log_params, **kwargs}
    try:
        yield
    finally:
        storage.log_params = old_log_params


def get_global_log_params():
    return getattr(storage, 'log_params', {})
