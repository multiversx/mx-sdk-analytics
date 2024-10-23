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
from multiversx_usage_analytics_tool.utils import (PackagesRegistry, Reports,
                                                   combine_pdfs,
                                                   get_environment_var,
                                                   get_pyppeteer_page,
                                                   is_empty_page,
                                                   select_report,
                                                   select_target_json_file)


async def capture_pdfs(temp_dir: str, selected_file: str) -> List[str]:
    wait_for_radio_selection_to_load_time = WAIT_FOR_RADIO_COMPONENT_LOAD
    wait_for_tabs_content_to_load_time = WAIT_FOR_TABS_COMPONENT_LOAD

    tab_ids = [repo.repo_name.replace('.', '-') for repo in PackagesRegistry if Reports.BLUE.value in repo.reports]
    organizations = [item.value.name for item in EcosystemConfiguration]

    async with async_playwright() as p:
        browser, page = await get_pyppeteer_page(p, Reports.BLUE.value)

        # click on selected file
        output = await select_report(page, selected_file)
        pdf_files = [output]

        await page.wait_for_selector('#organization-selector input[type="radio"]')
        radio_buttons = await page.query_selector_all('#organization-selector input[type="radio"]')

        # Loop through each radio button (organization)
        for idx, radio in enumerate(radio_buttons):
            await radio.click()
            await page.wait_for_timeout(wait_for_radio_selection_to_load_time)

            # Loop through each tab (package registry)
            for tab_id in tab_ids:
                await page.click(f'#{tab_id}')
                await page.wait_for_selector(f'#{tab_id}', timeout=10000)
                await page.wait_for_timeout(wait_for_tabs_content_to_load_time)

                is_empty = await is_empty_page(page)
                if is_empty:
                    print(f"Empty PDF for organization {organizations[idx]}, tab {tab_id}: not saved")
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

                print(f"Saved PDF for organization {organizations[idx]}, tab {tab_id}: {pdf_file}")

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
    selected_json = select_target_json_file(Reports.BLUE.value)
    asyncio.run(export_dash_report_to_pdf(selected_json))
