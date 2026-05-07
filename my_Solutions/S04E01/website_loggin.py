from playwright.sync_api import sync_playwright


def get_OKO_cookie(url: str, login: str, psw: str, api_key: str|None = None):
    
    with sync_playwright() as p:
    
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        page.goto(url)

        page.fill("input[name='login']", login)
        page.fill("input[name='password']", psw)
        if api_key: 
            page.fill("input[name='access_key']", api_key)
        page.click("button[type='submit']")

        page.wait_for_load_state("networkidle")

        cookies = context.cookies()

        browser.close()

        return cookies
    
