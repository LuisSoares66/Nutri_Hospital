import os
from functools import wraps
from flask import (
    Blueprint, render_template, request,
    redirect, url_for, flash, session
)

auth_bp = Blueprint("auth", __name__)


def _admin_pass() -> str:
    """
    Senha do administrador vinda do Render (Environment Variables).
    Configure no Render: ADMIN_PASS=suasenha
    """
    return (os.getenv("ADMIN_PASS") or "").strip()


def is_admin_logged() -> bool:
    return bool(session.get("is_admin") is True)


def admin_required(view_func):
    """
    Decorator para proteger rotas: só admin logado acessa.
    Se não estiver logado, manda para /admin/login.
    """
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if not is_admin_logged():
            # guarda para onde o usuário queria ir
            next_url = request.path
            return redirect(url_for("auth.admin_login", next=next_url))
        return view_func(*args, **kwargs)

    return wrapper


@auth_bp.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    """
    Página de login do admin.
    """
    if request.method == "POST":
        password = (request.form.get("password") or "").strip()

        if not _admin_pass():
            flash("ADMIN_PASS não configurada no Render.", "error")
            return redirect(url_for("auth.admin_login"))

        if password != _admin_pass():
            flash("Senha inválida.", "error")
            return redirect(url_for("auth.admin_login"))

        session["is_admin"] = True
        flash("Admin logado com sucesso.", "success")

        next_url = request.args.get("next") or url_for("main.hospitais")
        return redirect(next_url)

    # GET
    return render_template("admin_login.html")


@auth_bp.route("/admin/logout", methods=["GET"])
def admin_logout():
    session.pop("is_admin", None)
    flash("Você saiu do modo administrador.", "success")
    return redirect(url_for("main.hospitais"))
