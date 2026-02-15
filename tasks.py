import os
import shutil
from datetime import datetime
from uuid import UUID

from celery.schedules import crontab

import analytics
from analytics import Analytics, AnalyticsB2C
from celery_settings import celery
from creating_links import CreatingLinks
import logging
from methods import get_date_from_redis
from db import r
from regru_task.regru_task import CrmUpdatesHandler

log = logging.getLogger(os.getenv('APP_NAME'))


@celery.task()
def sync_analytics():
    analytics = Analytics(None, None)
    analytics.update_b2b_data()
    log.info("Sync finished successfully")
    return 200, "Sync finished successfully"


@celery.task()
def sync_analytics_b2c():
    analytics = AnalyticsB2C(None, None)
    analytics.update_b2c_data()
    log.info("Sync finished successfully")
    return 200, "Sync finished successfully"


@celery.task()
def create_links_from_photos(filename, file_uuid: UUID):
    links = CreatingLinks(filename, file_uuid)
    xlsx_path = links.run()
    return 200, f"Links created successfully, xlsx_path={xlsx_path}"


@celery.task()
def expire_old_links():
    path = "./media_compressed"
    now = datetime.now()
    removed_folders = []
    active_folders = []
    for folder in os.listdir(path):
        expiration_date = get_date_from_redis(folder)
        if not expiration_date:
            log.warning(f"Folder {folder} has no expiration date")
            continue
        elif now > expiration_date:
            folder_path = f"./media_compressed/{folder}"
            xlsx_path = f"./xlsx_files/{folder}.xlsx"
            shutil.rmtree(folder_path) if os.path.exists(folder_path) else ...
            os.remove(xlsx_path) if os.path.exists(xlsx_path) else ...
            r.delete(folder)
            removed_folders.append(folder)
        else:
            active_folders.append(folder)

    return (
        200,
        f"Removed folders = {removed_folders}, active folders = {active_folders}",
    )


@celery.task()
def handle_crm_updates():
    try:
        CrmUpdatesHandler.update_status()
        log.info("CRM updates synced successfully")
        return 200, "CRM updates synced successfully"
    except Exception as exc:
        log.exception(exc)
        return 400, f"Error while handling updates form crm exc={exc}"
    

@celery.task()
def sync_analytics_b2c_last_month():
    analytics = AnalyticsB2C(None, None)
    analytics.sync_last_month()
    log.info("Sync finished successfully")
    return 200, "Sync finished successfully"


# @celery.task()
# def check_payment():
#     payment_checker = analytics.PaymentCheck


# @celery.task
# def delete_old_files(directory: str, days: int = 10):
#     now = time.time()
#     cutoff = now - (days * 86400)  # 86400 секунд в дне
#
#     deleted_files = []
#
#     if not os.path.isdir(directory):
#         return f"Directory not found: {directory}"
#
#     for filename in os.listdir(directory):
#         file_path = os.path.join(directory, filename)
#
#         if os.path.isfile(file_path):
#             file_mtime = os.path.getmtime(file_path)
#
#             if file_mtime < cutoff:
#                 try:
#                     os.remove(file_path)
#                     deleted_files.append(filename)
#                 except Exception as e:
#                     print(f"Error deleting {file_path}: {e}")
#
#     return f"Deleted files: {deleted_files}"



@celery.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(
        crontab(hour="1", minute=30), sync_analytics.s()
    )
    sender.add_periodic_task(
        crontab(hour="*/1", minute=0), sync_analytics_b2c_last_month.s()
    )
    sender.add_periodic_task(
        crontab(hour="*/1", minute=30), expire_old_links.s()  # every hour at 30 minutes
    )
    sender.add_periodic_task(
        crontab(minute="*/3"), handle_crm_updates.s()  # every 5 minutes
    )
