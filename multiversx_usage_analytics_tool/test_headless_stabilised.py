import asyncio
from pyppeteer import launch


async def main():
    try:
        browser = await launch(headless=True, args=['--no-sandbox', '--disable-setuid-sandbox'])
        page = await browser.newPage()
        await page.goto('https://example.com')
        await asyncio.sleep(5)  # Keep it open for 5 seconds
        await browser.close()
        print('Response OK')
    except:
        print('Browser error')
asyncio.get_event_loop().run_until_complete(main())