
import json
import time
from datetime import datetime

from playwright.sync_api import Page, Playwright, sync_playwright

from config import Config

config = Config()



def _run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    
    page = context.new_page()
    context.grant_permissions(["clipboard-read", "clipboard-write"])
    page.goto("https://idleontoolbox.com/?profile=mochui")
    page.get_by_role("button", name="Consent").click()
    page.get_by_role("link", name="DATA").click()
    page.get_by_role("button", name="Dismiss privacy and legal").click()
    clipboard_text_str = get_data(page)

    if clipboard_text_str == "null": 
        page.reload()
        time.sleep(10)
        clipboard_text_str = get_data(page)

    clipboard_text = json.loads(clipboard_text_str)
    file_name = f"idle_on_data_{datetime.now().strftime("%Y-%m-%d")}"
    with open(config.data_folder / f"{file_name}.json", "w") as file:
        json.dump(clipboard_text,file, indent=4)

    # ---------------------
    context.close()
    browser.close()

def get_data(page:Page)->str:
    page.get_by_role("button", name="Copy").click()
    clipboard_text_str = page.evaluate("navigator.clipboard.readText()")
    return clipboard_text_str

def get_data_from_public_toolbox():
    with sync_playwright() as playwright:
        _run(playwright)


if __name__ == "__main__":
    get_data_from_public_toolbox()