import os
import platform
import subprocess
from datetime import datetime
from app.opensearch.client import health_check as opensearch_health

def get_system_info():
    return {
        "os": f"{platform.system()} {platform.release()}",
        "python": platform.python_version(),
        "hostname": platform.node(),
        "uptime": get_uptime()
    }

def get_uptime():
    try:
        with open('/proc/uptime', 'r') as f:
            uptime_seconds = float(f.readline().split()[0])
            days = int(uptime_seconds // 86400)
            hours = int((uptime_seconds % 86400) // 3600)
            return f"{days}d {hours}h"
    except:
        return "unknown"

def get_service_versions():
    versions = {}
    
    # OpenSearch version
    opensearch_info = opensearch_health()
    if opensearch_info["status"] == "healthy":
        versions["opensearch"] = opensearch_info["version"]
    else:
        versions["opensearch"] = "unavailable"
    
    # Python packages
    try:
        import fastapi
        versions["fastapi"] = fastapi.__version__
    except:
        versions["fastapi"] = "unknown"
    
    return versions

def get_rules_info():
    sigma_count = 0
    sigma_updated = "N/A"
    chainsaw_count = 0
    chainsaw_updated = "N/A"
    
    # Count Sigma rules
    sigma_dir = "/opt/casescope/tools/sigma/rules"
    if os.path.exists(sigma_dir):
        try:
            for root, dirs, files in os.walk(sigma_dir):
                sigma_count += len([f for f in files if f.endswith('.yml')])
            # Get last modified time
            import time
            mtime = os.path.getmtime(sigma_dir)
            sigma_updated = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M")
        except:
            pass
    
    # Chainsaw rules (placeholder - would count actual rules)
    chainsaw_dir = "/opt/casescope/tools/chainsaw"
    if os.path.exists(chainsaw_dir):
        chainsaw_count = 1  # Chainsaw binary exists
        try:
            import time
            mtime = os.path.getmtime(chainsaw_dir)
            chainsaw_updated = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M")
        except:
            pass
    
    return {
        "sigma_count": sigma_count,
        "sigma_updated": sigma_updated,
        "chainsaw_count": chainsaw_count,
        "chainsaw_updated": chainsaw_updated
    }
