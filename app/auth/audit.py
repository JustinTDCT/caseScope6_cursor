import os
from datetime import datetime

LOG_DIR = "/opt/casescope/logs"
os.makedirs(LOG_DIR, exist_ok=True)
LOGIN_LOG = os.path.join(LOG_DIR, "Logins.log")
AUDIT_LOG = os.path.join(LOG_DIR, "Audit.log")
ADMIN_LOG = os.path.join(LOG_DIR, "Admin.log")

def log_login(username: str, ip: str, ua: str, host: str):
    ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    with open(LOGIN_LOG, "a") as f:
        f.write(f"{ts} | LOGIN | user={username} ip={ip} ua=\"{ua}\" host={host}\n")

def log_logout(username: str, ip: str, ua: str, host: str):
    ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    with open(LOGIN_LOG, "a") as f:
        f.write(f"{ts} | LOGOUT | user={username} ip={ip} ua=\"{ua}\" host={host}\n")

def log_audit(username: str, action: str, details: str = "", ip: str = ""):
    ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    with open(AUDIT_LOG, "a") as f:
        f.write(f"{ts} | AUDIT | user={username} action={action} details=\"{details}\" ip={ip}\n")

def log_admin(username: str, action: str, details: str = "", ip: str = ""):
    ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    with open(ADMIN_LOG, "a") as f:
        f.write(f"{ts} | ADMIN | user={username} action={action} details=\"{details}\" ip={ip}\n")
