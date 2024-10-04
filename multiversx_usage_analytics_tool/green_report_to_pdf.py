import asyncio
from math import ceil
import os
from pathlib import Path
import tempfile
from typing import List

from PyPDF2 import PdfMerger
from dotenv.main import load_dotenv
from pyppeteer import launch

from multiversx_usage_analytics_tool.constants import GREEN_PDF_SAVE_WAIT_FOR_DROPDOWN_COMPONENT_LOAD, GREEN_PDF_SAVE_WAIT_FOR_RADIO_COMPONENT_LOAD, GREEN_PDF_SAVE_WAIT_FOR_TABS_COMPONENT_LOAD, GREEN_REPORT_PORT
from multiversx_usage_analytics_tool.utils import Language

from ecosystem_configuration import EcosystemConfiguration


async def capture_pdfs(temp_dir: str, selected_file: str) -> List[str]:
    wait_for_radio_selection_to_load_time = GREEN_PDF_SAVE_WAIT_FOR_RADIO_COMPONENT_LOAD
    wait_for_tabs_content_to_load_time = GREEN_PDF_SAVE_WAIT_FOR_TABS_COMPONENT_LOAD
    wait_for_dropdown_selection_to_load_time = GREEN_PDF_SAVE_WAIT_FOR_DROPDOWN_COMPONENT_LOAD

    browser = await launch(
        headless=True,
        handleSIGINT=False,
        handleSIGTERM=False,
        handleSIGHUP=False
    )
    page = await browser.newPage()
    await page.setViewport({'width': 1440, 'height': 1080})

    tab_ids = [item.value.name for item in EcosystemConfiguration]
    languages: List[str] = [item.lang_name for item in Language]
    DASH_APP_URL = f'http://0.0.0.0:{GREEN_REPORT_PORT}/'
    await page.goto(DASH_APP_URL)

    # click on selected file received from dash
    file_selector_id = 'file-selector'
    await page.waitForSelector(f'#{file_selector_id}')
    if selected_file:
        desired_value = selected_file.split('/')[-1]  # extract file name without path
        await page.click(f'#{file_selector_id} .Select-control')
        await page.waitForSelector('.Select-menu-outer')

        files = await page.evaluate('''() => {
            let elements = document.querySelectorAll('.VirtualizedSelectOption');
            let options_text = [];
            elements.forEach(option => options_text.push(option.textContent));
            return options_text;
        }''')
        desired_index = None
        for index, option in enumerate(files):
            if desired_value in option:
                desired_index = index
                break

        if desired_index is not None:
            option_selector = f'.Select-menu-outer .VirtualizedSelectOption:nth-child({desired_index + 1})'
            await page.click(option_selector)
            page.waitFor(wait_for_dropdown_selection_to_load_time)

    # Get the selected json file name
    selected_value: str = await page.evaluate(f'''
        document.querySelector("#{file_selector_id}").textContent;
    ''')
    print(f"Target report: {selected_value}")
    file_name = selected_value.split('.')[0]  # extract name without extension
    output = f'{file_name}.pdf' if 'green' in selected_value else 'green_combined.pdf'

    pdf_files = [output]

    await page.waitForSelector('#language-filter input[type="radio"]')
    radio_buttons = await page.querySelectorAll('#language-filter input[type="radio"]')

    await page.waitForSelector('#org-selector')
    tabs = await page.querySelectorAll('#org-selector .tab')

    # Loop through the tabs and get the ids
    tab_ids = []
    for tab in tabs:
        tab_id = await page.evaluate('(tab) => tab.id', tab)
        tab_ids.append(tab_id)

    # Loop through each tab (organization)
    for tab_id in tab_ids:

        # Loop through each radio button (language)
        for idx, radio in enumerate(radio_buttons):
            await radio.click()
            await page.waitFor(wait_for_radio_selection_to_load_time)

            await page.click(f'#{tab_id}')
            await page.waitForSelector(f'#{tab_id}', {'timeout': 10000})
            await page.waitFor(wait_for_tabs_content_to_load_time)

            height = '1080px'
            body_handle = await page.querySelector('body')
            if body_handle:
                bounding_box = await body_handle.boundingBox()
                if bounding_box:
                    height = str(ceil(bounding_box['height'])) + 'px'

            # Save each tab's content as a PDF
            pdf_file = os.path.join(temp_dir, f'report_{idx}_{tab_id}.pdf')
            pdf_files.append(pdf_file)
            await page.pdf({
                'path': pdf_file,
                'format': 'A4',
                'landscape': True,
                'printBackground': True,
                'width': '1440px',
                'height': f'{height}'
            })
            print(f"Saved PDF for language {'All' if idx == 0 else languages[idx - 1]}, tab {tab_id}: {pdf_file}")

    await browser.close()
    return pdf_files


def combine_pdfs(pdf_files: List[str], output_pdf: str):
    merger = PdfMerger()

    for pdf_file in pdf_files:
        merger.append(pdf_file)

    merger.write(output_pdf)
    merger.close()
    print(f"Combined PDF saved as: {output_pdf}")


async def export_dash_report_to_pdf(selected_file: str = ''):
    with tempfile.TemporaryDirectory() as temp_dir:
        pdf_files = await capture_pdfs(temp_dir, selected_file)
        load_dotenv()

        rep_folder = os.environ.get("REPORT_FOLDER")
        output_pdf = Path(rep_folder if rep_folder else ".") / f"{pdf_files[0]}"
        combine_pdfs(pdf_files[1:], str(output_pdf))

    return "done"

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(export_dash_report_to_pdf())
