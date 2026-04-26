from flask import Flask, render_template, request, redirect, url_for, make_response
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

app = Flask(__name__)
app.config["SECRET_KEY"] = "replace-this-with-a-random-secret-key"
app.config["AUTH_TOKEN_MAX_AGE"] = 3600  # seconds

serializer = URLSafeTimedSerializer(app.config["SECRET_KEY"])

# Simple user database for demonstration
VALID_USERS = {
    "tobias": "P@ssw0rd",
    "eva": "P@ssw0rd",
}


def generate_auth_token(username: str) -> str:
    return serializer.dumps({"username": username})


def verify_auth_token(token: str) -> str | None:
    try:
        data = serializer.loads(token, max_age=app.config["AUTH_TOKEN_MAX_AGE"])
        return data.get("username")
    except (BadSignature, SignatureExpired):
        return None


def login_required(view):
    def wrapped_view(*args, **kwargs):
        auth_token = request.cookies.get("auth_token")
        username = verify_auth_token(auth_token) if auth_token else None
        if not username:
            return redirect(url_for("login", next=request.path))
        return view(username, *args, **kwargs)

    wrapped_view.__name__ = view.__name__
    return wrapped_view


@app.route("/login", methods=["GET", "POST"])
def login():
    auth_token = request.cookies.get("auth_token")
    if auth_token and verify_auth_token(auth_token):
        return redirect(url_for("main"))

    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        expected_password = VALID_USERS.get(username)

        if expected_password and password == expected_password:
            token = generate_auth_token(username)
            response = make_response(redirect(url_for("main")))
            response.set_cookie(
                "auth_token",
                token,
                httponly=True,
                samesite="Lax",
                max_age=app.config["AUTH_TOKEN_MAX_AGE"],
            )
            return response
        error = "Invalid username or password."

    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    response = make_response(redirect(url_for("login")))
    response.delete_cookie("auth_token")
    return response


@app.route("/")
@login_required
def main(username: str):
    return render_template("main.html", username=username)


if __name__ == "__main__":
    app.run(debug=True)
