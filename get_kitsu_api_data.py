from json import dumps
import requests
from dotenv import load_dotenv
import os

load_dotenv()


def main():
    if not (refresh_token := os.environ.get("KITSU_REFRESH_TOKEN", "")):
        refresh_token = input(
            "Enter your refresh token (leave empty to use username/password): "
        )
    if refresh_token:
        r = requests.post(
            "https://kitsu.io/api/oauth/token",
            json={"grant_type": "refresh_token", "refresh_token": refresh_token},
        )
    else:
        if not (username := os.environ.get("KITSU_USERNAME", "")):
            username = input("Enter your username: ")
        if not (password := os.environ.get("KITSU_PASSWORD", "")):
            password = input("Enter your password: ")
        r = requests.post(
            "https://kitsu.io/api/oauth/token",
            json={
                "grant_type": "password",
                "username": username,
                "password": password,
            },
        )
    data = r.json()
    if not r.ok:
        print(f"Error: {data}")
        return
    print(f"KITSU_REFRESH_TOKEN={dumps(data['refresh_token'])}")
    print(f"KITSU_ACCESS_TOKEN={dumps(data['access_token'])}")
    print(f'KITSU_EXPIRES_AT={data["created_at"] + data["expires_in"]}')


if __name__ == "__main__":
    main()
