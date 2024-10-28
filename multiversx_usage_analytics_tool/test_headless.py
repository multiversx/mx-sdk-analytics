import asyncio

from playwright.async_api import async_playwright


async def main():
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            DASH_APP_URL = 'http://0.0.0.0:8052'
            # await page.goto('https://example.com')
            await page.goto(DASH_APP_URL)
            file_selector_id = 'file-selector'
            await page.wait_for_selector(f'#{file_selector_id}')
            await asyncio.sleep(2)  # Keep it open for 2 seconds
            await browser.close()
            print('Response OK')
    except Exception as e:
        print('Browser error:', e)

# Run the main function using asyncio
if __name__ == "__main__":
    asyncio.run(main())
