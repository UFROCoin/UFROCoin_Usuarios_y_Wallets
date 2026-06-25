from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_env_example_documents_dynamic_signing_variables():
    env_example = (PROJECT_ROOT / ".env.example").read_text(encoding="utf-8")

    assert "SECRET_KEY=<your_secret_key>" in env_example
    assert "JWT_ALGORITHM=HS256" in env_example
    assert "JWT_EXPIRE_HOURS=24" in env_example


def test_env_example_documents_resend_email_variables():
    env_example = (PROJECT_ROOT / ".env.example").read_text(encoding="utf-8")

    assert "RESEND_API_KEY=<your_resend_api_key>" in env_example
    assert 'RESEND_FROM_EMAIL="UFROCoin <no-reply@ufrocoin.email>"' in env_example
    assert "RESEND_RESET_SUBJECT=Recuperacion de contrasena UFROCoin" in env_example
    assert "PASSWORD_RESET_BASE_URL=https://app.ufrocoin.cl/reset-password" in env_example
    assert "RESEND_TIMEOUT_SECONDS=10" in env_example


def test_docker_compose_uses_mongodb_44_and_api_signing_env():
    compose = (PROJECT_ROOT / "docker-compose.yml").read_text(encoding="utf-8")

    assert compose.count("image: mongo:4.4") == 2
    assert "SECRET_KEY: ${SECRET_KEY}" in compose
    assert "JWT_ALGORITHM: ${JWT_ALGORITHM}" in compose
    assert "JWT_EXPIRE_HOURS: ${JWT_EXPIRE_HOURS}" in compose


def test_docker_compose_passes_resend_email_env_to_api():
    compose = (PROJECT_ROOT / "docker-compose.yml").read_text(encoding="utf-8")

    assert "RESEND_API_KEY: ${RESEND_API_KEY:-}" in compose
    assert "RESEND_FROM_EMAIL: ${RESEND_FROM_EMAIL:-UFROCoin <no-reply@ufrocoin.email>}" in compose
    assert "RESEND_RESET_SUBJECT: ${RESEND_RESET_SUBJECT:-Recuperacion de contrasena UFROCoin}" in compose
    assert "PASSWORD_RESET_BASE_URL: ${PASSWORD_RESET_BASE_URL:-http://localhost:5173/reset-password}" in compose
    assert "RESEND_TIMEOUT_SECONDS: ${RESEND_TIMEOUT_SECONDS:-10}" in compose


def test_mongo_init_waits_for_replica_set_primary():
    compose = (PROJECT_ROOT / "docker-compose.yml").read_text(encoding="utf-8")

    assert "if (status.ok !== 1)" in compose
    assert "rs.initiate({_id: 'rs0'" in compose
    assert "rs.isMaster().ismaster" in compose
