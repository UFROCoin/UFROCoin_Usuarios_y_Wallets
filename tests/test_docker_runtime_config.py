from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_env_example_documents_dynamic_signing_variables():
    env_example = (PROJECT_ROOT / ".env.example").read_text(encoding="utf-8")

    assert "SECRET_KEY=<your_secret_key>" in env_example
    assert "JWT_ALGORITHM=HS256" in env_example
    assert "JWT_EXPIRE_HOURS=24" in env_example


def test_docker_compose_uses_mongodb_44_and_api_signing_env():
    compose = (PROJECT_ROOT / "docker-compose.yml").read_text(encoding="utf-8")

    assert compose.count("image: mongo:4.4") == 2
    assert "SECRET_KEY: ${SECRET_KEY}" in compose
    assert "JWT_ALGORITHM: ${JWT_ALGORITHM}" in compose
    assert "JWT_EXPIRE_HOURS: ${JWT_EXPIRE_HOURS}" in compose


def test_mongo_init_waits_for_replica_set_primary():
    compose = (PROJECT_ROOT / "docker-compose.yml").read_text(encoding="utf-8")

    assert "if (status.ok !== 1)" in compose
    assert "rs.initiate({_id: 'rs0'" in compose
    assert "rs.isMaster().ismaster" in compose
