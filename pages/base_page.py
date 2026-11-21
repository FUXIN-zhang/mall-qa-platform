from playwright.sync_api import Page


class BasePage:
    def __init__(self, page: Page):
        self.page = page

    def open(self, url: str):
        self.page.goto(url, wait_until="domcontentloaded")

    def fill(self, selector: str, text: str):
        locator = self.page.locator(selector)
        locator.wait_for(state="visible", timeout=8000)
        locator.fill(text)

    def click(self, selector: str):
        locator = self.page.locator(selector)
        locator.wait_for(state="visible", timeout=8000)
        locator.click()

    def get_attribute(self, selector: str, attr_name: str) -> str | None:
        locator = self.page.locator(selector)
        locator.wait_for(state="visible", timeout=8000)
        return locator.get_attribute(attr_name)