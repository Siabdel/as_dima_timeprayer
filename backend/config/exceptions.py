"""
Handler d'exceptions DRF global.

Toutes les réponses d'erreur renvoient un JSON cohérent :
    {"error": {"code": "...", "message": "...", "details": {...}}}
Les erreurs non gérées par DRF (exceptions Python, 500) restent gérées par
Django et sont journalisées ; le handler DRF ne les masque pas.
"""
from rest_framework.views import exception_handler

# Correspondance statut HTTP -> code d'erreur interne par défaut.
DEFAULT_ERROR_CODES = {
    400: "validation_error",
    401: "unauthorized",
    403: "permission_denied",
    404: "not_found",
    405: "method_not_allowed",
    406: "not_acceptable",
    409: "conflict",
    410: "gone",
    415: "unsupported_media_type",
    429: "throttled",
    500: "server_error",
    503: "service_unavailable",
}


def custom_exception_handler(exc, context):
    """Enveloppe les erreurs DRF dans le format {"error": {...}}."""
    response = exception_handler(exc, context)
    if response is None:
        return None

    data = response.data
    code = DEFAULT_ERROR_CODES.get(response.status_code, "error")

    details = None
    if isinstance(data, dict):
        # Certaines exceptions DRF embarquent leur propre code (ex. SimpleJWT).
        if "code" in data:
            code = data["code"]
        details = {k: v for k, v in data.items() if k != "detail"}

    if isinstance(data, dict) and "detail" in data:
        message = str(data["detail"])
    elif details:
        # Erreurs de validation par champ : message générique + détail par champ.
        message = "Certaines données sont invalides."
    elif data:
        message = str(data)
    else:
        message = "Une erreur est survenue."

    error = {"code": code, "message": message}
    if details:
        error["details"] = details

    response.data = {"error": error}
    return response
