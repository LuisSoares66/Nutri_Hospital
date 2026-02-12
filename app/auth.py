import os
from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, flash, session

auth_bp = Blueprint("auth", __name__)

def _admin_user() -> str:
    return (os.getenv("ADMIN_USER") or "admin").strip()

def _admin_pass() -> str:
    # precisa estar configurado no Render (Environment)
    return (os.getenv("ADMIN_PASS") or "").strip()

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("is_admin"):
            flash("Acesso restrito ao administrador. Faça login.", "error")
            return redirect(url_for("auth.admin_login", next=request.path))
        return f(*args, **kwargs)
    return decorated


@auth_bp.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = (request.form.get("password") or "").strip()

        if not _admin_pass():
            flash("ADMIN_PASS não configurada no Render.", "error")
            return redirect(url_for("auth.admin_login"))

        if username == _admin_user() and password == _admin_pass():
            session["is_admin"] = True
            flash("Login admin realizado com sucesso.", "success")
            next_url = request.args.get("next") or url_for("main.hospitais")
            return redirect(next_url)

        flash("Usuário ou senha inválidos.", "error")
        return redirect(url_for("auth.admin_login"))

    # GET -> mostra a página
    return render_template("admin_login.html")


@auth_bp.route("/admin/logout", methods=["GET"])
def admin_logout():
    session.pop("is_admin", None)
    flash("Você saiu do modo administrador.", "info")
    return redirect(url_for("main.hospitais"))
