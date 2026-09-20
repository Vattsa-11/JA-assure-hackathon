from playwright.sync_api import sync_playwright


def check_frontend():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        print("Navigating to frontend...")
        page.goto("http://localhost:3000/leads")
        print("Waiting for network to be idle...")
        page.wait_for_load_state("networkidle")
        print("Extracting text...")
        text = page.inner_text("body")
        print("DOM Text:")
        print(text)
        browser.close()

if __name__ == '__main__':
    check_frontend()
