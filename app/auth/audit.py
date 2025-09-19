import os
from datetime import datetime

LOG_DIR = "/opt/casescope/logs"
os.makedirs(LOG_DIR, exist_ok=True)
LOGIN_LOG = os.path.join(LOG_DIR, "Logins.log")

def log_login(username: str, ip: str, ua: str, host: str):
    ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    with open(LOGIN_LOG, "a") as f:
        f.write(f"{ts} | LOGIN | user={username} ip={ip} ua=\"{ua}\" host={host}\n")

def log_logout(username: str, ip: str, ua: str, host: str):
    ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    with open(LOGIN_LOG, "a") as f:
        f.write(f"{ts} | LOGOUT | user={username} ip={ip} ua=\"{ua}\" host={host}\n")
