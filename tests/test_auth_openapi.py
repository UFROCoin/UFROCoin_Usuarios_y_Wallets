from src.main import app


def _responses_for(path, method="post"):
    return app.openapi()["paths"][path][method]["responses"]


def test_forgot_password_openapi_documents_standard_responses():
    responses = _responses_for("/api/users/forgot-password")
    response_500 = responses["500"]

    assert responses["200"]["content"]["application/json"]["example"] == {
        "success": True,
        "message": "Si el correo está registrado, recibirás un enlace para restablecer tu contraseña.",
        "data": {},
        "error": {"code": "", "details": ""},
    }
    assert responses["400"]["content"]["application/json"]["example"]["error"]["code"] == "VALIDATION_ERROR"
    assert "Resend" in response_500["description"]
    assert response_500["content"]["application/json"]["example"]["error"]["code"] == "EMAIL_DELIVERY_ERROR"
    examples = response_500["content"]["application/json"]["examples"]
    assert examples["timeout"]["value"]["error"]["code"] == "EMAIL_DELIVERY_TIMEOUT"
    assert examples["provider_not_configured"]["value"]["error"]["code"] == "EMAIL_PROVIDER_NOT_CONFIGURED"


def test_reset_password_openapi_documents_error_codes():
    responses = _responses_for("/api/users/reset-password")

    assert responses["200"]["content"]["application/json"]["example"]["error"] == {
        "code": "",
        "details": "",
    }
    assert responses["400"]["content"]["application/json"]["example"]["error"]["code"] == "VALIDATION_ERROR"
    assert responses["401"]["content"]["application/json"]["example"]["error"]["code"] == "INVALID_OR_EXPIRED_TOKEN"
    assert responses["500"]["content"]["application/json"]["example"]["error"]["code"] == "DATABASE_ERROR"


def test_get_me_openapi_documents_response_and_unauthorized_error():
    responses = _responses_for("/api/users/me", method="get")

    assert responses["200"]["content"]["application/json"]["example"]["data"]["history"] == []
    assert responses["200"]["content"]["application/json"]["example"]["data"]["wallet_address"]
    assert responses["401"]["content"]["application/json"]["example"]["success"] is False
    assert responses["401"]["content"]["application/json"]["example"]["error"]["code"] == "UNAUTHORIZED"
