# client/meet_bot.py
import asyncio
from playwright.async_api import async_playwright
import os
import subprocess

MEET_URL = os.getenv("MEET_URL", "https://meet.google.com/your-meet-code")
EMAIL = os.getenv("GOOGLE_EMAIL")
PASSWORD = os.getenv("GOOGLE_PASS")

async def join_meet():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=[
            "--use-fake-ui-for-media-stream",
            "--use-fake-device-for-media-stream",
            "--no-sandbox",
            "--disable-gpu",
            "--use-fake-ui-for-media-stream",
            "--allow-file-access-from-files",
            "--enable-logging",
        ])
        context = await browser.new_context()
        page = await context.new_page()

        # --- 1. Login to Google ---
        await page.goto("https://accounts.google.com/")
        await page.fill("input[type=email]", EMAIL)
        await page.click("#identifierNext")
        await page.wait_for_selector("input[type=password]")
        await page.fill("input[type=password]", PASSWORD)
        await page.click("#passwordNext")
        await page.wait_for_timeout(3000)

        # --- 2. Join Meet ---
        await page.goto(MEET_URL)
        await page.wait_for_timeout(5000)

        # Turn off camera & mic
        await page.keyboard.press("Control+D")  # mute mic
        await page.keyboard.press("Control+E")  # disable camera
        await page.wait_for_timeout(2000)

        # Click “Join now”
        join_button = await page.query_selector("text='Join now'")
        if join_button:
            await join_button.click()
        else:
            # Fallback for different Meet UI variants
            await page.locator("button:has-text('Join now')").click()
        print("✅ Joined Meet")

        # --- 3. Capture system audio (with PyAV or other) ---
        # Here, use virtual device or system “Stereo Mix”.
        # Example: record 1 minute using PyAV, then send to backend.
        subprocess.Popen(["python", "client/hybrid_bot.py"])

        # Stay in meet until manually closed or timeout
        await asyncio.sleep(60)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(join_meet())
