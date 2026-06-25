from ai_analytics_hub.core.extensions import db
from ai_analytics_hub.core.security import verify_password
from ai_analytics_hub.domain.models import User


def test_admin_console_manages_users(client, app):
    login_response = client.post(
        "/login",
        data={"email": "admin@example.com", "password": "Password123!"},
        follow_redirects=True,
    )

    assert login_response.status_code == 200
    assert b"Analytics Platform" in login_response.data

    page_response = client.get("/admin/users")
    assert page_response.status_code == 200
    assert b"User Management" in page_response.data

    create_response = client.post(
        "/admin/users",
        data={
            "action": "create-user",
            "full_name": "Executive Viewer",
            "email": "viewer@example.com",
            "password": "ViewerPass123!",
            "role": "viewer",
        },
        follow_redirects=True,
    )

    assert create_response.status_code == 200
    assert b"viewer@example.com" in create_response.data

    with app.app_context():
        created_user = db.session.query(User).filter_by(email="viewer@example.com").one()
        created_user_id = created_user.id
        assert created_user.role == "viewer"
        assert created_user.is_active is True

    update_response = client.post(
        "/admin/users",
        data={
            "action": "update-user",
            "user_id": str(created_user_id),
            "full_name": "Lead Analyst",
            "email": "lead.analyst@example.com",
            "role": "analyst",
            "is_active": "on",
        },
        follow_redirects=True,
    )

    assert update_response.status_code == 200
    assert b"lead.analyst@example.com" in update_response.data

    reset_response = client.post(
        "/admin/users",
        data={
            "action": "reset-password",
            "user_id": str(created_user_id),
            "new_password": "SecureReset456!",
        },
        follow_redirects=True,
    )

    assert reset_response.status_code == 200

    with app.app_context():
        updated_user = db.session.get(User, created_user_id)
        assert updated_user is not None
        assert updated_user.full_name == "Lead Analyst"
        assert updated_user.email == "lead.analyst@example.com"
        assert updated_user.role == "analyst"
        assert verify_password(updated_user.password_hash, "SecureReset456!")
