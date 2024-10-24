import asyncio
import os
import tempfile
from pathlib import Path
from typing import List

from playwright.async_api import async_playwright

from multiversx_usage_analytics_tool.constants import (
    WAIT_FOR_RADIO_COMPONENT_LOAD, WAIT_FOR_TABS_COMPONENT_LOAD)
from multiversx_usage_analytics_tool.ecosystem_configuration import \
    EcosystemConfiguration
from multiversx_usage_analytics_tool.utils import (Languages, Reports,
                                                   combine_pdfs,
                                                   get_environment_var,
                                                   get_playwright_page,
                                                   is_empty_page,
                                                   select_report,
                                                   select_target_json_file)


async def capture_pdfs(temp_dir: str, selected_file: str) -> List[str]:
    wait_for_radio_selection_to_load_time = WAIT_FOR_RADIO_COMPONENT_LOAD
    wait_for_tabs_content_to_load_time = WAIT_FOR_TABS_COMPONENT_LOAD

    tab_ids = [item.value.name for item in EcosystemConfiguration]
    languages: List[str] = [item.value.lang_name for item in Languages]

    async with async_playwright() as p:
        browser, page = await get_playwright_page(p, Reports.GREEN.value)

        # click on selected file
        output = await select_report(page, selected_file)
        pdf_files = [output]

        await page.wait_for_selector('#language-filter input[type="radio"]')
        radio_buttons = await page.query_selector_all('#language-filter input[type="radio"]')

        await page.wait_for_selector('#org-selector')
        tabs = await page.query_selector_all('#org-selector .tab')

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
                await page.wait_for_timeout(wait_for_radio_selection_to_load_time)

                await page.click(f'#{tab_id}')
                await page.wait_for_selector(f'#{tab_id}', timeout=10000)
                await page.wait_for_timeout(wait_for_tabs_content_to_load_time)

                is_empty = await is_empty_page(page)
                if is_empty:
                    print(f"Empty PDF for language {'All' if idx == 0 else languages[idx - 1]}, tab {tab_id}: not saved")
                    continue

                # Save each tab's content as a PDF
                pdf_file = os.path.join(temp_dir, f'report_{idx}_{tab_id}.pdf')
                pdf_files.append(pdf_file)
                await page.pdf(
                    path=pdf_file,
                    format='A4',
                    landscape=True,
                    print_background=True,
                )
                print(f"Saved PDF for language {'All' if idx == 0 else languages[idx - 1]}, tab {tab_id}: {pdf_file}")

        await browser.close()
    return pdf_files


async def export_dash_report_to_pdf(selected_file: str = ''):
    with tempfile.TemporaryDirectory() as temp_dir:
        pdf_files = await capture_pdfs(temp_dir, selected_file)

        rep_folder = get_environment_var("REPORT_FOLDER")
        output_pdf = Path(rep_folder if rep_folder else ".") / f"{pdf_files[0]}"
        combine_pdfs(pdf_files[1:], str(output_pdf))

    return "done"

if __name__ == "__main__":
    selected_json = select_target_json_file(Reports.GREEN.value)
    asyncio.run(export_dash_report_to_pdf(selected_json))
