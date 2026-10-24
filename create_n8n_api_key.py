import asyncio
from playwright.async_api import async_playwright

async def create_api_key():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        # Navigate to n8n
        print("Navigating to n8n...")
        await page.goto("http://localhost:5678")
        await page.wait_for_load_state("networkidle")
        
        # Wait for and click on Settings menu
        print("Looking for settings...")
        try:
            # Try to find settings menu - n8n typically has a settings gear
            await page.wait_for_selector('text=Settings', timeout=5000)
            await page.click('text=Settings')
            await page.wait_for_load_state("networkidle")
        except Exception as e:
            print(f"Could not find Settings directly: {e}")
            # Try navigating through the menu
            await page.click('text⟩')  # n8n menu button
        
        # Navigate to API Keys section
        print("Navigating to API Keys...")
        try:
            await page.click('text=API keys')
        except:
            await page.wait_for_selector('text=API keys', timeout=5000)
            await page.click('text=API keys')
        await page.wait_for_load_state("networkidle")
        
        # Click to add new API key
        print("Adding new API key...")
        await page.click('text=Add key')
        await page.wait_for_selector('input[placeholder*="key"]', timeout=5000)
        
        # Generate a random key
        import secrets
        new_key = secrets.token_hex(16)
        print(f"Generated key: {new_key}")
        
        # Fill in the key name and value
        await page.fill('input[placeholder*="key"]', new_key)
        await page.fill('input[placeholder*="name"]', 'ai-orchestrator-automated')
        
        # Save
        await page.click('text=Save')
        await page.wait_for_selector('text=API keys', timeout=5000)
        
        print("API key created successfully!")
        
        # Verify the key works
        print("Testing the API key...")
        headers = {
            "X-N8N-API-KEY": new_key,
            "Content-Type": "application/json"
        }
        resp = await page.request().put(
            "http://localhost:5678/api/v1/workflows/paB78BKlV4STecAT",
            headers=headers,
            json={"active": True}
        )
        print(f"Activation response status: {resp.status}")
        print(f"Activation response body: {await resp.text()}")
        
        await browser.close()

asyncio.run(create_api_key())
