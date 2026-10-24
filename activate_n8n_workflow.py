import os, sys, json, time, subprocess, secrets

# Configuration
N8N_URL = "http://localhost:5678"
WORKFLOW_ID = "paB78BKlV4STecAT"
ENV_FILE = ".env"
API_KEY_ENV = "N8N_API_KEY"

def load_api_key():
    # Try from environment variable first
    key = os.getenv(API_KEY_ENV)
    if key:
        return key
    # Try from .env file
    if os.path.exists(ENV_FILE):
        with open(ENV_FILE) as f:
            for line in f:
                if line.startswith(API_KEY_ENV + "="):
                    return line.strip().split("=", 1)[1]
    return None

def save_api_key(key):
    # Append or replace N8N_API_KEY in .env
    lines = []
    if os.path.exists(ENV_FILE):
        with open(ENV_FILE) as f:
            lines = f.readlines()
    new_lines = []
    found = False
    for l in lines:
        if l.startswith(API_KEY_ENV + "="):
            new_lines.append(f"{API_KEY_ENV}={key}\n")
            found = True
        else:
            new_lines.append(l)
    if not found:
        new_lines.append(f"{API_KEY_ENV}={key}\n")
    with open(ENV_FILE, "w") as f:
        f.writelines(new_lines)

def ensure_api_key():
    key = load_api_key()
    if key:
        print("Using existing API key from env/.env")
        return key
    # Generate a random 32-character hex key
    key = secrets.token_hex(16)
    print(f"Generated new API key: {key}")
    save_api_key(key)
    return key

def kill_existing_n8n():
    # Find any node processes running n8n and kill them (Windows)
    try:
        result = subprocess.check_output(["tasklist", "//FI", "IMAGENAME eq node.exe"], text=True)
        lines = result.strip().split('\n')
        for line in lines:
            if 'node.exe' in line:
                parts = line.split()
                if len(parts) >= 2:
                    pid = parts[1]
                    try:
                        subprocess.run(["taskkill", "//PID", pid, "//F"], check=True)
                        print(f"Killed n8n process {pid}")
                    except:
                        pass
    except Exception as e:
        print(f"No existing n8n process found or kill failed: {e}")

def start_n8n(key):
    env = os.environ.copy()
    env[API_KEY_ENV] = key
    # Start n8n in background - use full path to npx.cmd on Windows
    # Don't capture stdout/stderr to avoid blocking
    npx_path = r"H:\Program Files\nodejs\npx.cmd"
    proc = subprocess.Popen([npx_path, "n8n", "start"], env=env, 
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                           creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
    # Wait for it to be ready
    print("Waiting for n8n to start...")
    for i in range(30):
        time.sleep(1)
        try:
            import requests
            r = requests.get(N8N_URL, timeout=2)
            if r.status_code == 200:
                print("n8n is up and reachable.")
                return proc
        except:
            pass
        if i % 5 == 0:
            print(f"  Still waiting... ({i+1}/30)")
    print("n8n failed to start within 30 seconds")
    return proc

def activate_workflow(key):
    import requests
    headers = {
        "X-N8N-API-KEY": key,
        "Content-Type": "application/json"
    }
    url = f"{N8N_URL}/api/v1/workflows/{WORKFLOW_ID}"
    resp = requests.put(url, headers=headers, json={"active": True})
    print("Activate response status:", resp.status_code)
    print("Body:", resp.text)
    return resp

def test_webhook():
    import requests
    data = {
        "tenant_id": "test-tenant-001",
        "action": "create_product",
        "payload": {"name": "Final Auto Test", "price": "99000"},
        "tg_chat_id": "123456789"
    }
    r = requests.post(f"{N8N_URL}/webhook/multi-tenant-woocommerce", json=data)
    print("Webhook test status:", r.status_code)
    print("Response body:", r.text)
    return r

if __name__ == "__main__":
    api_key = ensure_api_key()
    kill_existing_n8n()
    proc = start_n8n(api_key)
    # Give a little extra time for n8n to load workflows
    time.sleep(4)
    activate_resp = activate_workflow(api_key)
    webhook_resp = test_webhook()
    summary = {
        "api_key": api_key,
        "activate_status": activate_resp.status_code,
        "activate_body": activate_resp.text,
        "webhook_status": webhook_resp.status_code,
        "webhook_body": webhook_resp.text
    }
    print("---SUMMARY---")
    print(json.dumps(summary, ensure_ascii=False))
    # Keep process alive for a bit then exit (background process will be terminated when script ends)
    proc.terminate()
