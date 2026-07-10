import urllib.request
import json

def get_windows_hardware_status() -> dict:
    """
    Queries Radiograph's active host stream to extract Windows hardware telemetry.
    Returns safe fallback dictionary states if Radiograph faces socket errors or port locks.
    """
    url = "http://127.0.0"
    
    payload = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "get_cpu_status",
            "arguments": {}
        },
        "id": 1
    }
    
    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=2) as response:
            raw_data = json.loads(response.read().decode('utf-8'))
            
        if "result" in raw_data and "content" in raw_data["result"]:
            return {"status": "Online", "data": raw_data["result"]["content"]["text"]}
        return {"status": "Offline", "data": "Windows sensors offline: Radiograph endpoint returned unexpected layout format."}
        
    except Exception:
        # 👑 SAFE EXCEPTION ANCHOR: Return plain text warning strings to ensure worker JSON stays healthy
        return {
            "status": "Offline", 
            "data": "Windows hardware telemetry offline: Radiograph host socket blocked or port closed."
        }

if __name__ == "__main__":
    print(json.dumps(get_windows_hardware_status(), indent=2))
