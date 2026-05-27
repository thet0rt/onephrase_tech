import os
import json
import logging
import gspread
from datetime import datetime

log = logging.getLogger(os.getenv('APP_NAME'))

SETTINGS_SHEET = 'НАСТРОЙКИ'
SETTINGS_HEADERS = ['Код', 'Статус', 'Дата старта', 'Дата конца']
CONTEST_SHEET_HEADERS = ['№', 'Instagram ID', 'Никнейм', 'Дата']


def _get_spreadsheet():
    with open('google_creds.json', 'r') as f:
        creds = json.load(f)
    gc = gspread.service_account_from_dict(creds)
    return gc.open_by_key(os.getenv('CONTEST_SPREADSHEET_ID'))


def _fmt_dt(dt: datetime) -> str:
    return dt.strftime('%d.%m.%Y %H:%M')


def init_contest_sheet(code: str, started_at: datetime):
    """Create a new worksheet for the contest and add a row to НАСТРОЙКИ."""
    try:
        sh = _get_spreadsheet()

        try:
            settings_ws = sh.worksheet(SETTINGS_SHEET)
        except gspread.WorksheetNotFound:
            settings_ws = sh.add_worksheet(title=SETTINGS_SHEET, rows=100, cols=4)
            settings_ws.append_row(SETTINGS_HEADERS)

        try:
            sh.worksheet(code)
            log.warning(f'Worksheet {code} already exists, skipping creation')
        except gspread.WorksheetNotFound:
            ws = sh.add_worksheet(title=code, rows=1000, cols=4)
            ws.append_row(CONTEST_SHEET_HEADERS)

        settings_ws.append_row([code, 'active', _fmt_dt(started_at), ''])
        log.info(f'Contest sheet initialised: {code}')
    except Exception as exc:
        log.exception(f'Failed to init contest sheet {code}: {exc}')
        raise


def append_participant(code: str, number: int, messenger_id: str, display_name: str, registered_at: datetime):
    """Append a participant row to the contest worksheet."""
    try:
        sh = _get_spreadsheet()
        ws = sh.worksheet(code)
        ws.append_row([number, messenger_id, display_name, _fmt_dt(registered_at)])
        log.info(f'Participant {messenger_id} appended to sheet {code}')
    except Exception as exc:
        log.exception(f'Failed to append participant to sheet {code}: {exc}')
        raise
