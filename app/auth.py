from functools import wraps
from flask import request, Response, current_app


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization

        user = current_app.config.get("ADMIN_USER", "admin")
        password = current_app.config.get("ADMIN_PASS", "8mVS1v8dUxzZkWGm35ag2hYU5V5Ixfy0")

        if not auth or auth.username != user or auth.password != password:
            return Response(
                "Acesso restrito",
                401,
                {"WWW-Authenticate": 'Basic realm="Admin"'},
            )

        return f(*args, **kwargs)

    return decorated
