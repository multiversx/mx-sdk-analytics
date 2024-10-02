import os
import tempfile
from typing import List

from PyPDF2 import PdfMerger
from pyppeteer import launch

from multiversx_usage_analytics_tool.constants import BLUE_REPORT_PORT
from multiversx_usage_analytics_tool.utils import PackagesRegistry, Reports


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

    # Wait for the radio items to be available (organization-selector)
    await page.waitForSelector('#organization-selector input[type="radio"]')

    # Get all radio buttons
    radio_buttons = await page.querySelectorAll('#organization-selector input[type="radio"]')

    # Ensure we found the radio buttons
    if not radio_buttons:
        print("No radio buttons found!")
        return []

    # Loop through each radio button (organization)
    for idx, radio in enumerate(radio_buttons):
        # Click the radio button to select it
        await radio.click()
        await page.waitFor(2000)  # Wait for page content to update based on organization selection

        # Now loop through the tabs
        for tab_id in tab_ids:
            await page.click(f'#{tab_id}')
            await page.waitForSelector(f'#{tab_id}', {'timeout': 10000})
            await page.waitFor(5000)

            # Save each tab's content as a PDF
            pdf_file = os.path.join(temp_dir, f'report_{idx}_{tab_id}.pdf')
            pdf_files.append(pdf_file)
            await page.pdf({
                'path': pdf_file,
                'format': 'A4',
                'landscape': True,
                'printBackground': True,
                'width': '1440px',
                'height': '1080px'
            })
            print(f"Saved PDF for organization {idx}, tab {tab_id}: {pdf_file}")

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

# Run the export
# asyncio.get_event_loop().run_until_complete(export_dash_report_to_pdf())
