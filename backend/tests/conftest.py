import sys
import os
import pytest

# Ensure backend root is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from app.extensions import db as _db
from app.models.user import User

@pytest.fixture(scope="session")
def app():
    app = create_app("testing")
    with app.app_context():
        _db.create_all()
        yield app
        _db.drop_all()

@pytest.fixture(scope="function")
def db_session(app):
    with app.app_context():
        _db.session.begin_nested()
        yield _db.session
        _db.session.rollback()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def test_user(app):
    with app.app_context():
        user = User.query.filter_by(username="testdev").first()
        if not user:
            user = User(username="testdev", email="testdev@example.com")
            user.set_password("SecurePass123!")
            _db.session.add(user)
            _db.session.commit()
        return user

@pytest.fixture
def auth_headers(client, test_user):
    resp = client.post("/api/auth/login", json={
        "identifier": "testdev@example.com",
        "password": "SecurePass123!"
    })
    token = resp.get_json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def second_user_headers(client, app):
    with app.app_context():
        user2 = User.query.filter_by(username="seconduser").first()
        if not user2:
            user2 = User(username="seconduser", email="second@example.com")
            user2.set_password("SecondPass123!")
            _db.session.add(user2)
            _db.session.commit()
    resp = client.post("/api/auth/login", json={
        "identifier": "second@example.com",
        "password": "SecondPass123!"
    })
    token = resp.get_json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
