#!/usr/bin/env python3
"""
Playwright script to automate n8n UI and create an API key.
"""

import asyncio
import os
import sys
import re
from pathlib import Path

async def create_api_key():
    from playwright.async_api import async_playwright
    
    api_key = None
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            # Navigate to n8n
            print("Navigating to n8n...")
            await page.goto("http://localhost:5678/editor", wait_until="networkidle", timeout=60000)
            
            # Wait for the sidebar to load
            print("Waiting for sidebar...")
            await page.wait_for_selector('[data-test-id="main-sidebar-settings"]', timeout=60000)
            
            # Click on Settings in sidebar
            print("Clicking Settings in sidebar...")
            await page.click('[data-test-id="main-sidebar-settings"]', timeout=10000)
            
            # Wait for settings page to load
            await page.wait_for_load_state("networkidle", timeout=30000)
            await page.wait_for_timeout(3000)
            
            # Get page content to debug
            content = await page.content()
            test_ids = re.findall(r'data-test-id="([^"]+)"', content)
            print(f"Settings page test-ids: {sorted(set(test_ids))}")
            
            # Find API Keys tab - could be in tabs or navigation
            api_keys_selectors = [
                '[data-test-id="settings-api-keys"]',
                '[data-test-id="tabs-api-keys"]',
                'a[href*="api-keys"]',
                'button:has-text("API Keys")',
                '[role="tab"]:has-text("API Keys")',
            ]
            
            api_keys_clicked = False
            for selector in api_keys_selectors:
                try:
                    await page.click(selector, timeout=5000)
                    api_keys_clicked = True
                    print(f"Clicked API Keys with selector: {selector}")
                    break
                except:
                    continue
            
            if not api_keys_clicked:
                print("Could not find API Keys tab, trying to navigate directly...")
                await page.goto("http://localhost:5678/settings/api-keys", wait_until="networkidle", timeout=60000)
            
            # Wait for API Keys page to load
            await page.wait_for_load_state("networkidle", timeout=30000)
            await page.wait_for_timeout(3000)
            
            # Debug: print page content
            content = await page.content()
            test_ids = re.findall(r'data-test-id="([^"]+)"', content)
            print(f"API Keys page test-ids: {sorted(set(test_ids))}")
            
            # Click "Create API Key" or "Add API Key" button
            print("Looking for Create API Key button...")
            create_key_selectors = [
                '[data-test-id="create-api-key-button"]',
                '[data-test-id="add-api-key-button"]',
                'button:has-text("Create API Key")',
                'button:has-text("Add API Key")',
                'button:has-text("New API Key")',
                'a:has-text("Create API Key")',
            ]
            
            create_clicked = False
            for selector in create_key_selectors:
                try:
                    await page.click(selector, timeout=5000)
                    create_clicked = True
                    print(f"Clicked Create API Key with selector: {selector}")
                    break
                except:
                    continue
            
            if not create_clicked:
                print("Could not find Create API Key button, searching all buttons...")
                buttons = await page.query_selector_all('button')
                for btn in buttons:
                    text = await btn.inner_text()
                    if ('create' in text.lower() or 'add' in text.lower() or 'new' in text.lower()) and ('key' in text.lower() or 'api' in text.lower()):
                        await btn.click()
                        create_clicked = True
                        print(f"Clicked button with text: {text}")
                        break
            
            if create_clicked:
                # Wait for modal/dialog to appear
                await page.wait_for_load_state("networkidle", timeout=10000)
                await page.wait_for_timeout(2000)
                
                # Fill in the name if there's an input
                name_input_selectors = [
                    '[data-test-id="api-key-name-input"]',
                    'input[name="name"]',
                    'input[placeholder*="name" i]',
                    'input[type="text"]',
                ]
                
                for selector in name_input_selectors:
                    try:
                        await page.fill(selector, "Auto-generated API Key", timeout=5000)
                        print(f"Filled name with selector: {selector}")
                        break
                    except:
                        continue
                
                # Click Save/Create button
                save_selectors = [
                    '[data-test-id="api-key-save-button"]',
                    '[data-test-id="create-api-key-confirm"]',
                    'button:has-text("Save")',
                    'button:has-text("Create")',
                    'button[type="submit"]',
                ]
                
                for selector in save_selectors:
                    try:
                        await page.click(selector, timeout=5000)
                        print(f"Clicked save with selector: {selector}")
                        break
                    except:
                        continue
                
                # Wait for the key to be displayed
                await page.wait_for_load_state("networkidle", timeout=10000)
                await page.wait_for_timeout(3000)
                
                # Get updated page content
                content = await page.content()
                
                # Extract the API key from the page
                key_selectors = [
                    '[data-test-id="api-key-value"]',
                    '[data-test-id="created-api-key"]',
                    '[data-test-id="api-key-token"]',
                    'code',
                    '.api-key-value',
                    'input[readonly]',
                ]
                
                for selector in key_selectors:
                    try:
                        elements = await page.query_selector_all(selector)
                        for element in elements:
                            key_text = await element.inner_text()
                            if not key_text:
                                key_text = await element.get_attribute("value")
                            if key_text and len(key_text) > 20:
                                api_key = key_text.strip()
                                print(f"Found API key with selector {selector}: {api_key[:20]}...")
                                break
                        if api_key:
                            break
                    except:
                        continue
                
                # If not found in specific elements, search the page for a long token
                if not api_key:
                    print("Searching page for API key...")
                    # Look for JWT-like tokens or long alphanumeric strings
                    jwt_matches = re.findall(r'eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+', content)
                    if jwt_matches:
                        api_key = jwt_matches[0]
                        print(f"Found JWT API key: {api_key[:20]}...")
                    else:
                        # Look for long alphanumeric strings (40+ chars)
                        long_matches = re.findall(r'[A-Za-z0-9]{40,}', content)
                        if long_matches:
                            api_key = long_matches[0]
                            print(f"Found long token: {api_key[:20]}...")
            
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await browser.close()
    
    return api_key

def main():
    api_key = asyncio.run(create_api_key())
    
    if api_key:
        # Save to .env file
        env_path = Path(".env")
        env_content = f"N8N_API_KEY={api_key}\n"
        
        if env_path.exists():
            with open(env_path, "r") as f:
                content = f.read()
            # Replace or add N8N_API_KEY
            if "N8N_API_KEY" in content:
                content = re.sub(r'N8N_API_KEY=.*', f'N8N_API_KEY={api_key}', content)
            else:
                content += f"\nN8N_API_KEY={api_key}\n"
            with open(env_path, "w") as f:
                f.write(content)
        else:
            with open(env_path, "w") as f:
                f.write(env_content)
        
        print(f"API Key saved to .env: {api_key[:20]}...")
        print(f"Full API Key: {api_key}")
        return 0
    else:
        print("Failed to create API key")
        return 1

if __name__ == "__main__":
    sys.exit(main())