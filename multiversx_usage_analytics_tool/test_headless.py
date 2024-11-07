import asyncio

from playwright.async_api import async_playwright

# Verifies that playwright is correctly installed


async def main():
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto('https://example.com')
            await asyncio.sleep(2)  # Keep it open for 2 seconds
            await browser.close()
            print('Response OK')
    except Exception as e:
        print('Browser error:', e)

# Run the main function using asyncio
if __name__ == "__main__":
    asyncio.run(main())
