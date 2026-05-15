from src.main import app


def _responses_for(path, method="post"):
    return app.openapi()["paths"][path][method]["responses"]


def test_forgot_password_openapi_documents_standard_responses():
    responses = _responses_for("/api/users/forgot-password")

    assert responses["200"]["content"]["application/json"]["example"] == {
        "success": True,
        "message": "Si el correo está registrado, recibirás un enlace para restablecer tu contraseña.",
        "data": {},
        "error": {"code": "", "details": ""},
    }
    assert responses["422"]["content"]["application/json"]["example"]["error"]["code"] == "VALIDATION_ERROR"
    assert responses["500"]["content"]["application/json"]["example"]["error"]["code"] == "DATABASE_ERROR"


def test_reset_password_openapi_documents_error_codes():
    responses = _responses_for("/api/users/reset-password")

    assert responses["200"]["content"]["application/json"]["example"]["error"] == {
        "code": "",
        "details": "",
    }
    assert responses["422"]["content"]["application/json"]["example"]["error"]["code"] == "VALIDATION_ERROR"
    assert responses["401"]["content"]["application/json"]["example"]["error"]["code"] == "INVALID_OR_EXPIRED_TOKEN"
    assert responses["500"]["content"]["application/json"]["example"]["error"]["code"] == "DATABASE_ERROR"
