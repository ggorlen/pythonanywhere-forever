#!/usr/bin/env python3

import os
import time
import traceback
import requests

BASE = "https://www.pythonanywhere.com"


def get_csrf_from_cookies(session: requests.Session) -> str:
    csrf = session.cookies.get("csrftoken")
    if not csrf:
        raise RuntimeError("Could not find csrftoken cookie")
    return csrf


def login(session: requests.Session, username: str, password: str):
    print("[2/4] Logging in")

    csrf = get_csrf_from_cookies(session)

    data = {
        "csrfmiddlewaretoken": csrf,
        "auth-username": username,
        "auth-password": password,
        "login_view-current_step": "auth",
    }

    headers = {
        "Referer": f"{BASE}/login/",
    }

    response = session.post(f"{BASE}/login/", headers=headers, data=data)

    if response.url != f"{BASE}/user/{username}/":
        raise RuntimeError("Login failed. Check credentials.")

    print("✓ Logged in")


def renew_webapp(session: requests.Session, username: str):
    print("[3/4] Opening Web tab")

    web_url = f"{BASE}/user/{username}/webapps/"
    session.get(web_url)

    csrf = get_csrf_from_cookies(session)

    print("[4/4] Extending webapp (3 months)")

    headers = {
        "Referer": web_url,
    }

    data = {
        "csrfmiddlewaretoken": csrf,
    }

    response = session.post(
        f"{BASE}/user/{username}/webapps/{username}.pythonanywhere.com/extend",
        headers=headers,
        data=data,
    )

    if response.status_code == 200 and response.url.endswith("/webapps/"):
        print("✓ Successfully extended webapp")
    else:
        raise RuntimeError("Failed to extend webapp")


def run():
    username = os.getenv("PA_USERNAME")
    password = os.getenv("PA_PASSWORD")

    if not username or not password:
        raise RuntimeError("Set PA_USERNAME and PA_PASSWORD environment variables")

    TRIES = 3

    for attempt in range(1, TRIES + 1):
        print(f"\nAttempt {attempt}/{TRIES}")

        try:
            session = requests.Session()

            # Step 1: Load login page (sets csrftoken cookie)
            print("[1/4] Getting login page")
            session.get(f"{BASE}/login/")

            # Step 2: Login
            login(session, username, password)

            # Step 3 & 4: Renew
            renew_webapp(session, username)

            print("\n🎉 Done.")
            return

        except Exception:
            print("Error occurred:")
            traceback.print_exc()

            if attempt < TRIES:
                print("Retrying in 60 seconds...\n")
                time.sleep(60)
            else:
                print("All attempts failed.")
                raise


if __name__ == "__main__":
    run()
