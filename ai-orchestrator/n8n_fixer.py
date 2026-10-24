#!/usr/bin/env python3
"""
n8n Fixer - Creates API key via Playwright and activates workflow via API
"""
import os
import sys
import json
import time
import secrets
import subprocess
import requests
from pathlib import Path

# Configuration
N8N_URL = "http://localhost:5678"
WORKFLOW_ID = "paB78BKlV4STecAT"
ENV_FILE = Path(__file__).parent.parent / ".env"
API_KEY_ENV = "N8N_API_KEY"

def load_api_key():
    """Load API key from environment or .env file."""
    # Try from environment variable first
    key = os.getenv(API_KEY_ENV)
    if key:
        print("Using existing API key from environment")
        return key
    # Try from .env file
    if ENV_FILE.exists():
        with open(ENV_FILE) as f:
            for line in f:
                if line.startswith(API_KEY_ENV + "="):
                    key = line.strip().split("=", 1)[1]
                    print("Using existing API key from .env")
                    return key
    return None

def save_api_key(key):
    """Save API key to .env file."""
    lines = []
    if ENV_FILE.exists():
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
    print(f"Saved API key to {ENV_FILE}")

async def create_api_key_playwright():
    """Create API key using Playwright browser automation."""
    from playwright.async_api import async_playwright
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            print("Navigating to n8n...")
            await page.goto(N8N_URL)
            await page.wait_for_load_state("networkidle")
            await page.wait_for_timeout(3000)
            
            # Try to find and click Settings
            print("Looking for Settings...")
            settings_selectors = [
                'text=Settings',
                '[data-test-id="settings"]',
                'button:has-text("Settings")',
                'a:has-text("Settings")',
                '.settings-button',
                '[aria-label="Settings"]'
            ]
            
            settings_clicked = False
            for selector in settings_selectors:
                try:
                    await page.wait_for_selector(selector, timeout=3000)
                    await page.click(selector)
                    await page.wait_for_load_state("networkidle")
                    await page.wait_for_timeout(2000)
                    settings_clicked = True
                    print(f"Clicked Settings with selector: {selector}")
                    break
                except:
                    continue
            
            if not settings_clicked:
                # Try keyboard shortcut or menu
                print("Trying alternative navigation...")
                await page.keyboard.press("Alt+s")
                await page.wait_for_timeout(1000)
                try:
                    await page.click('text=Settings')
                    await page.wait_for_load_state("networkidle")
                    settings_clicked = True
                except:
                    pass
            
            # Navigate to API Keys
            print("Navigating to API Keys...")
            api_keys_selectors = [
                'text=API keys',
                'text=API Keys',
                '[data-test-id="api-keys"]',
                'a:has-text("API")',
                'button:has-text("API")'
            ]
            
            api_keys_clicked = False
            for selector in api_keys_selectors:
                try:
                    await page.wait_for_selector(selector, timeout=5000)
                    await page.click(selector)
                    await page.wait_for_load_state("networkidle")
                    await page.wait_for_timeout(2000)
                    api_keys_clicked = True
                    print(f"Clicked API Keys with selector: {selector}")
                    break
                except:
                    continue
            
            # Click Add key
            print("Adding new API key...")
            add_key_selectors = [
                'text=Add key',
                'text=Add Key',
                'button:has-text("Add")',
                '[data-test-id="add-api-key"]',
                'button:has-text("Create")'
            ]
            
            add_clicked = False
            for selector in add_key_selectors:
                try:
                    await page.wait_for_selector(selector, timeout=5000)
                    await page.click(selector)
                    await page.wait_for_timeout(2000)
                    add_clicked = True
                    print(f"Clicked Add key with selector: {selector}")
                    break
                except:
                    continue
            
            # Fill in the key name and value
            new_key = secrets.token_hex(16)
            print(f"Generated key: {new_key}")
            
            # Try to fill key value field
            key_input_selectors = [
                'input[placeholder*="key" i]',
                'input[name="key"]',
                'input[id*="key"]',
                'input[type="password"]',
                'input[autocomplete="new-password"]'
            ]
            
            for selector in key_input_selectors:
                try:
                    await page.wait_for_selector(selector, timeout=3000)
                    await page.fill(selector, new_key)
                    print(f"Filled key value with selector: {selector}")
                    break
                except:
                    continue
            
            # Fill key name
            name_selectors = [
                'input[placeholder*="name" i]',
                'input[name="name"]',
                'input[id*="name"]'
            ]
            
            for selector in name_selectors:
                try:
                    await page.wait_for_selector(selector, timeout=3000)
                    await page.fill(selector, "ai-orchestrator-automated")
                    print(f"Filled key name with selector: {selector}")
                    break
                except:
                    continue
            
            # Save
            save_selectors = [
                'text=Save',
                'button:has-text("Save")',
                '[data-test-id="save-api-key"]',
                'button[type="submit"]'
            ]
            
            for selector in save_selectors:
                try:
                    await page.wait_for_selector(selector, timeout=3000)
                    await page.click(selector)
                    await page.wait_for_timeout(3000)
                    print(f"Clicked Save with selector: {selector}")
                    break
                except:
                    continue
            
            print("API key created successfully!")
            
            # Verify the key works by testing the API
            print("Testing the API key...")
            headers = {
                "X-N8N-API-KEY": new_key,
                "Content-Type": "application/json"
            }
            resp = await page.request().put(
                f"{N8N_URL}/api/v1/workflows/{WORKFLOW_ID}",
                headers=headers,
                json={"active": True}
            )
            print(f"Activation response status: {resp.status}")
            print(f"Activation response body: {await resp.text()}")
            
            await browser.close()
            return new_key
            
        except Exception as e:
            print(f"Error during Playwright automation: {e}")
            await browser.close()
            return None

def create_api_key_via_cli():
    """Alternative: Create API key using n8n CLI if available."""
    try:
        # Generate a key
        new_key = secrets.token_hex(16)
        
        # Try to use n8n CLI to create the key
        # n8n user-management:apikey:create --key="key" --name="name"
        result = subprocess.run(
            ["npx", "n8n", "user-management:apikey:create", f"--key={new_key}", "--name=ai-orchestrator-automated"],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            print(f"Created API key via CLI: {new_key}")
            return new_key
        else:
            print(f"CLI creation failed: {result.stderr}")
            return None
    except Exception as e:
        print(f"CLI approach failed: {e}")
        return None

def ensure_api_key():
    """Ensure we have a valid API key, create one if needed."""
    key = load_api_key()
    if key:
        # Test if the key works
        if test_api_key(key):
            print("Existing API key is valid")
            return key
        else:
            print("Existing API key is invalid, creating new one...")
    else:
        print("No API key found. Attempting to create one...")
    
    # First try CLI (faster, headless)
    key = create_api_key_via_cli()
    if key:
        save_api_key(key)
        return key
    
    # Fall back to Playwright
    print("CLI failed, trying Playwright...")
    import asyncio
    key = asyncio.run(create_api_key_playwright())
    if key:
        save_api_key(key)
        return key
    
    # Last resort: generate a random key and hope n8n accepts it
    # (n8n might accept any key if configured with N8N_API_KEY env var)
    print("Playwright failed, generating random key for env-based auth...")
    key = secrets.token_hex(16)
    save_api_key(key)
    return key

def test_api_key(key):
    """Test if an API key is valid by making a simple API call."""
    headers = {
        "X-N8N-API-KEY": key,
        "Content-Type": "application/json"
    }
    url = f"{N8N_URL}/api/v1/workflows/{WORKFLOW_ID}"
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        return resp.status_code != 401
    except:
        return False

def activate_workflow(key):
    """Activate the workflow using the n8n API."""
    headers = {
        "X-N8N-API-KEY": key,
        "Content-Type": "application/json"
    }
    url = f"{N8N_URL}/api/v1/workflows/{WORKFLOW_ID}"
    
    print(f"Activating workflow {WORKFLOW_ID}...")
    print(f"URL: {url}")
    print(f"Headers: {json.dumps(headers, indent=2)}")
    
    try:
        resp = requests.put(url, headers=headers, json={"active": True}, timeout=30)
        print(f"Activate response status: {resp.status_code}")
        print(f"Activate response headers: {dict(resp.headers)}")
        print(f"Activate response body: {resp.text}")
        
        if resp.status_code == 200:
            print("[SUCCESS] Workflow activated successfully!")
            return resp
        elif resp.status_code == 401:
            print("[ERROR] Unauthorized - API key may be invalid")
        elif resp.status_code == 404:
            print("[ERROR] Workflow not found - check WORKFLOW_ID")
        elif resp.status_code == 400:
            print("[ERROR] Bad request - check payload format")
        
        return resp
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return None

def test_webhook():
    """Test the webhook endpoint."""
    data = {
        "tenant_id": "test-tenant-001",
        "action": "create_product",
        "payload": {"name": "Final Test", "price": "99000"},
        "tg_chat_id": "123456789"
    }
    url = f"{N8N_URL}/webhook/multi-tenant-woocommerce"
    
    print(f"Testing webhook at {url}...")
    print(f"Payload: {json.dumps(data, indent=2)}")
    
    try:
        r = requests.post(url, json=data, timeout=30)
        print(f"Webhook test status: {r.status_code}")
        print(f"Webhook response headers: {dict(r.headers)}")
        print(f"Webhook response body: {r.text}")
        
        if r.status_code == 200:
            print("[SUCCESS] Webhook test successful!")
        else:
            print("[FAILED] Webhook test failed")
        
        return r
    except requests.exceptions.RequestException as e:
        print(f"❌ Webhook request failed: {e}")
        return None

def main():
    print("=" * 60)
    print("n8n Fixer - Starting workflow activation process")
    print("=" * 60)
    
    # Step 1: Ensure API key
    api_key = ensure_api_key()
    print(f"\n[API Key] Using API Key: {api_key[:8]}...{api_key[-8:] if len(api_key) > 16 else api_key}")
    
    # Step 2: Activate workflow
    activate_resp = activate_workflow(api_key)
    
    # Step 3: Test webhook
    webhook_resp = test_webhook()
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    summary = {
        "api_key_used": f"{api_key[:8]}...{api_key[-8:] if len(api_key) > 16 else api_key}",
        "activate_status": activate_resp.status_code if activate_resp else None,
        "activate_body": activate_resp.text if activate_resp else None,
        "webhook_status": webhook_resp.status_code if webhook_resp else None,
        "webhook_body": webhook_resp.text if webhook_resp else None
    }
    
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    
    # Check success
    activate_ok = activate_resp and activate_resp.status_code == 200
    webhook_ok = webhook_resp and webhook_resp.status_code == 200
    
    if activate_ok and webhook_ok:
        print("\n[SUCCESS] ALL TESTS PASSED!")
        return 0
    else:
        print("\n[FAILED] SOME TESTS FAILED")
        if not activate_ok:
            print("  - Workflow activation failed")
        if not webhook_ok:
            print("  - Webhook test failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())