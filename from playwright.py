import asyncio
import re
import requests
from playwright.async_api import async_playwright

# --- CONFIGURATION ---
TELEGRAM_TOKEN = "8638830876:AAFruklFCF0Ghy5zsa1Ih6ncLuyLmglm0tA"
CHAT_ID = "8203814996" 

URL_LIST = [
    "https://careers.qatarairways.com/global/SearchJobs/pilot?listFilterMode=1&jobRecordsPerPage=10&",
    "https://careers.qatarairways.com/global/SearchJobs/?listFilterMode=1&jobRecordsPerPage=10&"
]

def send_telegram(message):
    """Sends a formatted message to your Telegram bot."""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False
    }
    try:
        response = requests.post(url, data=payload)
        if response.status_code == 200:
            print("✅ Telegram alert sent successfully!")
        else:
            print(f"❌ Telegram failed: {response.text}")
    except Exception as e:
        print(f"❌ Connection error: {e}")

async def scan_url(context, url):
    """Scans a specific URL for JobDetail links using source code analysis."""
    page = await context.new_page()
    jobs_on_this_page = []
    try:
        print(f"Scanning: {url}")
        # Wait for the network to settle to ensure all dynamic links are rendered
        await page.goto(url, wait_until="networkidle", timeout=60000)
        await asyncio.sleep(4) # Brief pause for Avature scripts
        
        source_code = await page.content()
        # Regex to capture the specific JobDetail URL structure
        pattern = r'href="(https://careers.qatarairways.com/global/JobDetail/[^"]+)"'
        links = re.findall(pattern, source_code)
        
        for link in set(links):
            # Extract and clean the job title from the URL slug
            job_name = link.split('/')[-2].replace('-', ' ')
            jobs_on_this_page.append({"title": job_name.title(), "link": link})
    except Exception as e:
        print(f"❌ Error scanning {url}: {e}")
    finally:
        await page.close()
    return jobs_on_this_page

async def main():
    async with async_playwright() as p:
        # Running in headless mode (no browser window pops up)
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )

        total_results = []
        for url in URL_LIST:
            jobs = await scan_url(context, url)
            total_results.extend(jobs)

        # Remove duplicates found across different search queries
        unique_jobs = {j['link']: j['title'] for j in total_results}

        if unique_jobs:
            # Create a clean, readable message for your phone
            msg = "✈️ *QATAR AIRWAYS CAREER TRACKER*\n"
            msg += "───────────────────\n\n"
            for link, title in unique_jobs.items():
                msg += f"🔹 *{title}*\n🔗 [Apply / View Details]({link})\n\n"
            
            send_telegram(msg)
            print(f"Success! Sent {len(unique_jobs)} jobs to your Telegram.")
        else:
            print("No matching jobs found today.")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())