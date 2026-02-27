from __future__ import annotations

from flask import Flask, render_template

from demark.storage.db import Database


def create_app(db_path: str) -> Flask:
    app = Flask(__name__, template_folder="templates")
    db = Database(db_path)

    @app.get("/")
    def index():
        rows = db.list_signal_states()
        return render_template("index.html", rows=rows)

    return app
