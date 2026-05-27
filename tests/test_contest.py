import pytest
from unittest.mock import patch
from app import app as flask_app
from db import db as _db
from models import Contest, Participant, ContestStatus


@pytest.fixture(scope='session')
def app():
    flask_app.config['TESTING'] = True
    flask_app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    flask_app.config['WTF_CSRF_ENABLED'] = False
    flask_app.extensions.pop('sqlalchemy', None)
    _db.init_app(flask_app)
    with flask_app.app_context():
        _db.create_all()
        yield flask_app
        _db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture(autouse=True)
def clean_db(app):
    with app.app_context():
        _db.session.query(Participant).delete()
        _db.session.query(Contest).delete()
        _db.session.commit()
    yield


@patch('contest.routes.init_contest_sheet_task')
@patch('contest.routes.sync_participant_to_sheets')
def test_register_new_participant_returns_ok(mock_sync, mock_init, client):
    resp = client.post('/api/contest/register', data={
        'code': 'SUMMER',
        'messenger_id': '111',
        'display_name': 'user1'
    })
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['status'] == 'ok'
    assert data['number'] == 1


@patch('contest.routes.init_contest_sheet_task')
@patch('contest.routes.sync_participant_to_sheets')
def test_register_duplicate_returns_exists(mock_sync, mock_init, client):
    client.post('/api/contest/register', data={
        'code': 'SUMMER', 'messenger_id': '111', 'display_name': 'user1'
    })
    resp = client.post('/api/contest/register', data={
        'code': 'SUMMER', 'messenger_id': '111', 'display_name': 'user1'
    })
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['status'] == 'exists'
    assert data['number'] == 1


@patch('contest.routes.init_contest_sheet_task')
@patch('contest.routes.sync_participant_to_sheets')
def test_register_increments_number(mock_sync, mock_init, client):
    client.post('/api/contest/register', data={
        'code': 'SUMMER', 'messenger_id': '111', 'display_name': 'user1'
    })
    resp = client.post('/api/contest/register', data={
        'code': 'SUMMER', 'messenger_id': '222', 'display_name': 'user2'
    })
    data = resp.get_json()
    assert data['status'] == 'ok'
    assert data['number'] == 2


@patch('contest.routes.init_contest_sheet_task')
@patch('contest.routes.sync_participant_to_sheets')
def test_register_closed_contest_returns_closed(mock_sync, mock_init, client, app):
    with app.app_context():
        from datetime import datetime
        contest = Contest(code='WINTER', status=ContestStatus.INACTIVE, started_at=datetime.utcnow())
        _db.session.add(contest)
        _db.session.commit()

    resp = client.post('/api/contest/register', data={
        'code': 'WINTER', 'messenger_id': '333', 'display_name': 'user3'
    })
    assert resp.status_code == 200
    assert resp.get_json()['status'] == 'closed'


@patch('contest.routes.init_contest_sheet_task')
@patch('contest.routes.sync_participant_to_sheets')
def test_code_normalised_to_uppercase(mock_sync, mock_init, client):
    resp = client.post('/api/contest/register', data={
        'code': '  summer repost ', 'messenger_id': '444', 'display_name': 'user4'
    })
    data = resp.get_json()
    assert data['status'] == 'ok'
    resp2 = client.post('/api/contest/register', data={
        'code': 'Summer', 'messenger_id': '444', 'display_name': 'user4'
    })
    assert resp2.get_json()['status'] == 'exists'


def test_update_status_sets_inactive(client, app):
    with app.app_context():
        from datetime import datetime
        contest = Contest(code='PROMO', status=ContestStatus.ACTIVE, started_at=datetime.utcnow())
        _db.session.add(contest)
        _db.session.commit()

    resp = client.post('/api/contest/update_status', data={
        'code': 'PROMO', 'status': 'inactive'
    })
    assert resp.status_code == 200
    assert resp.get_json()['status'] == 'ok'

    with app.app_context():
        c = Contest.query.filter_by(code='PROMO').first()
        assert c.status == ContestStatus.INACTIVE
        assert c.ended_at is not None


def test_update_status_unknown_contest_returns_error(client):
    resp = client.post('/api/contest/update_status', data={
        'code': 'GHOST', 'status': 'inactive'
    })
    assert resp.status_code == 200
    assert resp.get_json()['status'] == 'error'
