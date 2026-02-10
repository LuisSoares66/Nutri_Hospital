from functools import wraps
from flask import (
    Blueprint, request, session,
    redirect, url_for, flash
)
from config import Config

auth_bp = Blueprint("auth", __name__)

# ==========================
# LOGIN ADMIN
# ==========================
@auth_bp.route("/admin/login", methods=["POST", "GET"])
def admin_login():
    if request.method == "POST":
        user = request.form.get("username")
        pwd = request.form.get("password")

        if user == Config.ADMIN_USER and pwd == Config.ADMIN_PASS:
            session["is_admin"] = True
            flash("Login admin realizado com sucesso.", "success")
            return redirect(url_for("main.hospitais"))

        flash("Usuário ou senha inválidos.", "error")

    return redirect(url_for("main.hospitais"))


# ==========================
# LOGOUT ADMIN
# ==========================
@auth_bp.route("/admin/logout")
def admin_logout():
    session.pop("is_admin", None)
    flash("Logout admin realizado.", "info")
    return redirect(url_for("main.hospitais"))


# ==========================
# DECORATOR DE PROTEÇÃO
# ==========================
def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("is_admin"):
            flash(
                "Acesso restrito ao administrador.",
                "error"
            )
            return redirect(url_for("main.hospitais"))
        return f(*args, **kwargs)
    return decorated
