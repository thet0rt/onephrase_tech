import logging
import os
from datetime import datetime

from flask import request, jsonify
from sqlalchemy.exc import IntegrityError

from db import db
from models import Contest, Participant, ContestStatus
from tasks import sync_participant_to_sheets, init_contest_sheet_task
from . import contest_bp
from .schemas import RegisterSchema, UpdateStatusSchema

log = logging.getLogger(os.getenv('APP_NAME'))

_register_schema = RegisterSchema()
_status_schema = UpdateStatusSchema()


def _normalise_code(raw: str) -> str:
    return raw.strip().split()[0].upper()


@contest_bp.post('/register')
def register():
    errors = _register_schema.validate(request.form)
    if errors:
        return jsonify({'status': 'error', 'message': str(errors)}), 400

    raw_code = request.form.get('code', '')
    messenger_id = request.form.get('messenger_id', '').strip()
    display_name = request.form.get('display_name', '').strip()
    code = _normalise_code(raw_code)

    try:
        early_response = None
        is_new_contest = False
        number = None
        contest_code = None
        started_at_iso = None
        registered_at_iso = None

        with db.session.begin():
            stmt = db.select(Contest).filter_by(code=code)
            if db.engine.dialect.name != 'sqlite':
                stmt = stmt.with_for_update()
            contest = db.session.execute(stmt).scalar_one_or_none()

            if contest is None:
                contest = Contest(
                    code=code,
                    status=ContestStatus.ACTIVE,
                    started_at=datetime.utcnow()
                )
                db.session.add(contest)
                db.session.flush()
                is_new_contest = True
            elif contest.status == ContestStatus.INACTIVE:
                early_response = jsonify({'status': 'closed'})

            if early_response is None:
                existing = db.session.execute(
                    db.select(Participant).filter_by(
                        contest_id=contest.id,
                        messenger_id=messenger_id
                    )
                ).scalar_one_or_none()

                if existing:
                    early_response = jsonify({'status': 'exists', 'number': existing.number})
                else:
                    count = db.session.execute(
                        db.select(db.func.count(Participant.id)).filter_by(contest_id=contest.id)
                    ).scalar()
                    number = count + 1
                    participant = Participant(
                        contest_id=contest.id,
                        messenger_id=messenger_id,
                        display_name=display_name,
                        number=number,
                        registered_at=datetime.utcnow()
                    )
                    db.session.add(participant)
                    contest_code = contest.code
                    started_at_iso = contest.started_at.isoformat()
                    registered_at_iso = participant.registered_at.isoformat()

        if early_response is not None:
            return early_response

        if is_new_contest:
            init_contest_sheet_task.delay(contest_code, started_at_iso)

        sync_participant_to_sheets.delay(
            contest_code, number, messenger_id, display_name, registered_at_iso
        )

        return jsonify({'status': 'ok', 'number': number})

    except IntegrityError:
        db.session.rollback()
        log.warning(f'Duplicate registration attempt: contest={code} messenger_id={messenger_id}')
        participant = Participant.query.join(Contest).filter(
            Contest.code == code,
            Participant.messenger_id == messenger_id
        ).first()
        if participant:
            return jsonify({'status': 'exists', 'number': participant.number})
        return jsonify({'status': 'error', 'message': 'integrity error'}), 500

    except Exception as exc:
        db.session.rollback()
        log.exception(f'Register error: {exc}')
        return jsonify({'status': 'error', 'message': str(exc)}), 500


@contest_bp.post('/update_status')
def update_status():
    errors = _status_schema.validate(request.form)
    if errors:
        return jsonify({'status': 'error', 'message': str(errors)}), 400

    code = request.form.get('code', '').strip().upper()
    status_str = request.form.get('status', '').strip().lower()

    contest = Contest.query.filter_by(code=code).first()
    if not contest:
        log.warning(f'update_status: contest not found: {code}')
        return jsonify({'status': 'error', 'message': f'contest {code} not found'})

    contest.status = ContestStatus.ACTIVE if status_str == 'active' else ContestStatus.INACTIVE
    if status_str == 'inactive' and contest.ended_at is None:
        contest.ended_at = datetime.utcnow()
    elif status_str == 'active':
        contest.ended_at = None

    db.session.commit()
    log.info(f'Contest {code} status updated to {status_str}')
    return jsonify({'status': 'ok'})
