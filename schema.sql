CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    full_name VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(32) NOT NULL DEFAULT 'analyst',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);

CREATE TABLE uploads (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    content_type VARCHAR(255) NOT NULL,
    storage_path VARCHAR(512) NOT NULL,
    checksum_sha256 VARCHAR(64) NOT NULL,
    file_size_bytes INTEGER NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'stored',
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);

CREATE TABLE jobs (
    id INTEGER PRIMARY KEY,
    upload_id INTEGER NULL REFERENCES uploads(id),
    requested_by_id INTEGER NOT NULL REFERENCES users(id),
    job_type VARCHAR(64) NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'queued',
    model_name VARCHAR(255) NULL,
    model_version VARCHAR(255) NULL,
    parameters_json JSON NULL,
    result_json JSON NULL,
    error_message TEXT NULL,
    started_at TIMESTAMP NULL,
    completed_at TIMESTAMP NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);

CREATE TABLE audit_events (
    id INTEGER PRIMARY KEY,
    actor_id INTEGER NULL REFERENCES users(id),
    action VARCHAR(128) NOT NULL,
    resource_type VARCHAR(64) NOT NULL,
    resource_id VARCHAR(128) NULL,
    ip_address VARCHAR(64) NULL,
    details_json JSON NULL,
    created_at TIMESTAMP NOT NULL
);

CREATE TABLE chat_sessions (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    title VARCHAR(255) NOT NULL DEFAULT 'New Conversation',
    provider VARCHAR(64) NOT NULL DEFAULT 'openrouter',
    model_name VARCHAR(255) NOT NULL DEFAULT 'openrouter/free',
    system_prompt TEXT NULL,
    last_message_at TIMESTAMP NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);

CREATE TABLE chat_messages (
    id INTEGER PRIMARY KEY,
    session_id INTEGER NOT NULL REFERENCES chat_sessions(id),
    role VARCHAR(32) NOT NULL,
    content TEXT NOT NULL,
    provider_message_id VARCHAR(255) NULL,
    input_tokens INTEGER NULL,
    output_tokens INTEGER NULL,
    created_at TIMESTAMP NOT NULL
);
