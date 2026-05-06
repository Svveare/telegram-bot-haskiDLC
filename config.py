import os
from dotenv import load_dotenv

load_dotenv()


def _parse_admin_ids(raw_admins: str) -> list[int]:
    admin_ids: list[int] = []
    for value in raw_admins.split(","):
        normalized = value.strip().strip("'\"")
        if normalized:
            admin_ids.append(int(normalized))
    return admin_ids


TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise RuntimeError("TOKEN is not set")

ADMIN_IDS = _parse_admin_ids(os.getenv("ADMINS", ""))

FUNPAY_URL = os.getenv("FUNPAY_URL", "https://funpay.com/")
PM_USERNAME = os.getenv("PM_USERNAME", "").strip()
