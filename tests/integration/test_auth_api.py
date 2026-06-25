def test_api_login_returns_jwt(client):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "Password123!"},
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["success"] is True
    assert "token" in payload["data"]
    assert payload["data"]["user"]["role"] == "admin"
