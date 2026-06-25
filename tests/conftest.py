import pytest

from ai_analytics_hub import create_app
from ai_analytics_hub.core.extensions import db
from ai_analytics_hub.core.security import hash_password
from ai_analytics_hub.domain.models import Role, User


@pytest.fixture()
def app():
    app = create_app("testing")
    with app.app_context():
        db.create_all()
        user = User(
            email="admin@example.com",
            full_name="Admin User",
            password_hash=hash_password("Password123!"),
            role=Role.ADMIN.value,
        )
        db.session.add(user)
        db.session.commit()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()
