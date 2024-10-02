# import asyncio
from typing import List
from pyppeteer import launch
import tempfile
import os
from PyPDF2 import PdfMerger
from multiversx_usage_analytics_tool.utils import PackagesRegistry, Reports
from multiversx_usage_analytics_tool.constants import BLUE_REPORT_PORT


async def capture_pdfs(temp_dir: str) -> List[str]:
    browser = await launch(
        headless=True,
        handleSIGINT=False,
        handleSIGTERM=False,
        handleSIGHUP=False
    )
    page = await browser.newPage()
    await page.setViewport({'width': 1440, 'height': 1080})

    tab_ids = [repo.repo_name.replace('.', '-') for repo in PackagesRegistry if Reports.BLUE in repo.reports]

    DASH_APP_URL = f'http://0.0.0.0:{BLUE_REPORT_PORT}/'
    await page.goto(DASH_APP_URL)

    pdf_files = []

    await page.waitForSelector(f'#{tab_ids[0]}')
    radio_buttons = await page.querySelectorAll('input[name="organization-selector"]')

    # Loop through and click each radio button
    for radio_button in radio_buttons:
        await radio_button.click()
        await page.waitFor(1000)  # Optional delay between clicks
        print(radio_button)
    await browser.close()
    for tab_id in tab_ids:
        await page.click(f'#{tab_id}')

        await page.waitForSelector(f'#{tab_id}', {'timeout': 10000})
        await page.waitFor(5000)

        pdf_file = os.path.join(temp_dir, f'report_{tab_id}.pdf')
        pdf_files.append(pdf_file)
        await page.pdf({
            'path': pdf_file,
            'format': 'A4',
            'landscape': True,
            'printBackground': True,
            'width': '1440px',
            'height': '1080px'
        })
        print(f"Saved PDF for {tab_id}: {pdf_file}")

    await browser.close()
    return pdf_files


def combine_pdfs(pdf_files: List[str], output_pdf: str):
    merger = PdfMerger()

    for pdf_file in pdf_files:
        merger.append(pdf_file)

    merger.write(output_pdf)
    merger.close()
    print(f"Combined PDF saved as: {output_pdf}")


async def export_dash_report_to_pdf():
    with tempfile.TemporaryDirectory() as temp_dir:
        pdf_files = await capture_pdfs(temp_dir)
        output_pdf = "combined_report.pdf"
        combine_pdfs(pdf_files, output_pdf)
    return "done"

# asyncio.get_event_loop().run_until_complete(export_dash_report_to_pdf())
