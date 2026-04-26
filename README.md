# Flask Auth Token Demo

A simple Flask project with a login page that issues an auth token as an HTTP cookie.

## Setup

1. Create a virtual environment:

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Run the app:

   ```bash
   python app.py
   ```

4. Open `http://127.0.0.1:5000` in your browser.

## Credentials

- admin / password
- user / secret

## Notes

The auth token is created after login and stored in the `auth_token` cookie. Protected routes validate the token on each request.
