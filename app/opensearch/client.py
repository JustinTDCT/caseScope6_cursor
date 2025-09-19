from opensearchpy import OpenSearch
import os
from typing import Dict, Any, List

OPENSEARCH_URL = os.environ.get("OPENSEARCH_URL", "http://127.0.0.1:9200")

def get_opensearch_client():
    return OpenSearch(
        hosts=[OPENSEARCH_URL],
        http_auth=None,  # no auth for local single-node
        use_ssl=False,
        verify_certs=False,
        ssl_assert_hostname=False,
        ssl_show_warn=False,
    )

def get_case_index_name(case_id: int) -> str:
    return f"events-case-{case_id}-v1"

def create_case_index(client: OpenSearch, case_id: int) -> bool:
    index_name = get_case_index_name(case_id)
    if client.indices.exists(index=index_name):
        return True
    
    mapping = {
        "mappings": {
            "properties": {
                "timestamp": {"type": "date"},
                "event_id": {"type": "keyword"},
                "source": {"type": "keyword"},
                "host": {"type": "keyword"},
                "record_hash": {"type": "keyword"},
                "severity": {"type": "keyword"},
                "tags": {"type": "keyword"},
                "file_id": {"type": "integer"},
                "case_id": {"type": "integer"},
                "raw": {"type": "text"}
            }
        }
    }
    
    try:
        client.indices.create(index=index_name, body=mapping)
        return True
    except Exception:
        return False

def health_check() -> Dict[str, Any]:
    try:
        client = get_opensearch_client()
        info = client.info()
        return {
            "status": "healthy",
            "version": info.get("version", {}).get("number", "unknown"),
            "cluster_name": info.get("cluster_name", "unknown")
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
