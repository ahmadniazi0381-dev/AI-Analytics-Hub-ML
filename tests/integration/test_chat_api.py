def test_chat_session_and_message_flow(client):
    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "Password123!"},
    )
    token = login_response.get_json()["data"]["token"]
    headers = {"Authorization": f"Bearer {token}"}

    session_response = client.post(
        "/api/v1/chat/sessions",
        json={"title": "Strategy Review"},
        headers=headers,
    )
    assert session_response.status_code == 201
    session_payload = session_response.get_json()["data"]["session"]
    assert session_payload["title"] == "Strategy Review"

    message_response = client.post(
        f"/api/v1/chat/sessions/{session_payload['id']}/messages",
        json={"content": "How should we position this platform for enterprise analytics teams?"},
        headers=headers,
    )
    assert message_response.status_code == 200
    message_payload = message_response.get_json()["data"]
    assert message_payload["provider"] == "mock"
    assert "Mock assistant response" in message_payload["assistant_message"]["content"]
