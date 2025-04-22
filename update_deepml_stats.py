import requests
from bs4 import BeautifulSoup
import re
import os
import time # For potential delays if needed

# --- Selenium Imports ---
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager # Manages chromedriver installation

# --- Configuration ---
# !!! IMPORTANT: USE YOUR ACTUAL PROFILE URL !!!
PROFILE_URL = "https://www.deep-ml.com/profile/Y5llgZoBWpPVmkyEw0guauFb8IG2"
README_PATH = "README.md"
START_COMMENT = "<!-- START_DEEPML_STATS -->"
END_COMMENT = "<!-- END_DEEPML_STATS -->"
# --- End Configuration ---

def fetch_stats_with_wait(url):
    """
    Fetches stats using Selenium: waits for JS to load data, then scrapes.
    """
    stats = {
        "rank": "N/A", "solved": "N/A", "streak": "N/A",
        "fav_category": "N/A", "score": "N/A", "avatar_url": "",
        "username": "N/A", "email": "N/A", "github_url": "#",
        "linkedin_url": "#",
    }

    # --- Setup Selenium WebDriver ---
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new") # Use the new headless mode
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080") # Specify window size for consistency
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36") # Example User Agent

    driver = None
    try:
        print("Initializing WebDriver...")
        service = ChromeService(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        driver.set_page_load_timeout(30)

        print(f"Fetching URL with Selenium: {url}")
        driver.get(url)

        # --- WAIT for dynamic content ---
        # Wait for the H2 tag with the username inside the specific profile card div.
        # This indicates the API call finished and rendered the data.
        wait_timeout = 25 # Seconds
        print(f"Waiting up to {wait_timeout}s for profile data to render...")
        wait_selector = "div.bg-zinc-800\\/50.backdrop-blur-lg h2.text-xl" # CSS Selector for username H2 within the card
        try:
             WebDriverWait(driver, wait_timeout).until(
                 EC.presence_of_element_located((By.CSS_SELECTOR, wait_selector))
             )
             print("Data element (username H2) found. Page should be loaded.")
        except Exception as wait_error:
             print(f"Error: Timed out waiting for element '{wait_selector}'. Data might not have loaded or structure changed.")
             print(f"Wait Error: {wait_error}")
             # Optionally try to get source anyway for debugging
             # page_source = driver.page_source
             # print("Page source at timeout:", page_source[:2000])
             return stats # Return defaults if wait fails

        # Optional small delay just in case rendering needs a fraction more time
        # time.sleep(1)

        # --- Get Page Source AFTER waiting ---
        print("Getting page source after JS execution and wait...")
        page_source = driver.page_source
        # print(page_source) # Uncomment for full source debugging in Actions logs

        # --- Parse with BeautifulSoup ---
        print("Parsing fetched page source with BeautifulSoup...")
        soup = BeautifulSoup(page_source, 'html.parser')

        # --- Find the Profile Card (Selectors from previous successful attempt) ---
        profile_card = soup.find('div', class_='bg-zinc-800/50 backdrop-blur-lg')
        if not profile_card:
            print("Error: Could not find the main profile card div in the *rendered* HTML.")
            return stats

        print("Successfully found profile card div.")

        # --- Extract Info *ONLY WITHIN* the profile_card ---
        # (This is the same reliable extraction logic as before)

        # Header Info
        header_flex = profile_card.find('div', class_='flex items-center space-x-4 mb-6')
        if header_flex:
            avatar_span = header_flex.find('span', class_='relative flex shrink-0')
            if avatar_span:
                 avatar_img = avatar_span.find('img', class_='aspect-square h-full w-full')
                 if avatar_img and 'src' in avatar_img.attrs: stats['avatar_url'] = avatar_img['src']
            info_div = header_flex.find('div')
            if info_div and info_div != avatar_span:
                username_h2 = info_div.find('h2', class_='text-xl')
                if username_h2: stats['username'] = username_h2.text.strip()
                email_p = info_div.find('p', class_='text-sm text-zinc-400')
                if email_p: stats['email'] = email_p.text.strip()
                rank_div = info_div.find('div', class_='flex items-center mt-1 text-xs text-zinc-400')
                if rank_div:
                    rank_span = rank_div.find('span')
                    if rank_span:
                        match = re.search(r'Rank #(\d+)', rank_span.text)
                        if match: stats['rank'] = match.group(1)

        # Social Links
        social_links_div = profile_card.find('div', class_='flex space-x-3 mb-6')
        if social_links_div:
            github_a = social_links_div.find('a', {'aria-label': 'GitHub'})
            if github_a and 'href' in github_a.attrs: stats['github_url'] = github_a['href']
            linkedin_a = social_links_div.find('a', {'aria-label': 'LinkedIn'})
            if linkedin_a and 'href' in linkedin_a.attrs: stats['linkedin_url'] = linkedin_a['href']

        # Stats Grid
        stats_grid = profile_card.find('div', class_='grid grid-cols-2 gap-3')
        if stats_grid:
            stat_blocks = stats_grid.find_all('div', class_='relative overflow-hidden', recursive=False)
            for block in stat_blocks:
                h3 = block.find('h3', class_='text-xs font-medium text-zinc-400 mb-1')
                if h3:
                    h3_text = h3.text.strip()
                    if "Problems Solved" in h3_text:
                        p_tag = block.find('p', class_='text-2xl font-bold text-zinc-100')
                        if p_tag: stats['solved'] = p_tag.text.strip()
                    elif "Current Streak" in h3_text:
                        p_tag = block.find('p', class_='text-2xl font-bold text-zinc-100')
                        if p_tag:
                            match = re.search(r'(\d+)', p_tag.text)
                            stats['streak'] = match.group(1) if match else '0'
                    elif "Favorite Category" in h3_text:
                        p_tag = block.find('p', class_='text-sm font-medium text-zinc-100')
                        if p_tag: stats['fav_category'] = p_tag.text.strip()
                else: # Check for Flame Score structure
                    score_p = block.find('p', class_='mt-2 text-lg font-bold text-white')
                    if score_p: stats['score'] = score_p.text.strip()

        print("--- Final Parsed Stats ---")
        print(stats)
        print("--------------------------")
        return stats

    except Exception as e:
        print(f"An error occurred during Selenium execution or parsing: {e}")
        import traceback
        print(traceback.format_exc())
        return stats # Return defaults on error
    finally:
        if driver:
            print("Quitting WebDriver...")
            driver.quit()


# --- Function to generate README remains the same ---
def generate_new_readme(stats, readme_content):
    """Generates the new README content with updated stats."""
    # Ensure this function correctly uses the 'stats' dict to build the HTML table
    # (Using the version from previous answers)
    streak_text = f"{stats.get('streak', '0')} days"
    stats_table = f"""
<table align="center" width="350px" style="border: 1px solid #404040; border-radius: 12px; background-color: #262626; padding: 15px;">
  <tr>
    <td colspan="2">
      <table width="100%">
        <tr>
          <td width="70px" valign="top">
            <img src="{stats.get('avatar_url', '') or 'DEFAULT_AVATAR_URL'}" alt="{stats.get('username', 'User')}" width="64" height="64" style="border-radius: 50%; border: 2px solid #525252;" />
          </td>
          <td valign="top" style="padding-left: 10px;">
            <h2 style="margin: 0; color: #f5f5f5; font-size: 1.25rem; font-weight: 500;">{stats.get('username', 'N/A')}</h2>
            <p style="margin: 0; font-size: 0.875rem; color: #a3a3a3;">{stats.get('email', 'N/A')}</p>
            <p style="margin: 5px 0 0 0; font-size: 0.75rem; color: #a3a3a3;">
              🏆 Rank #{stats.get('rank', 'N/A')}
            </p>
            <p style="margin: 10px 0 0 0;">
              <a href="{stats.get('github_url', '#')}" target="_blank" rel="noopener noreferrer" aria-label="GitHub" style="display: inline-block; padding: 5px; background-color: #3f3f46; border-radius: 6px; margin-right: 5px; line-height: 0;"><img src="https://raw.githubusercontent.com/devicons/devicon/master/icons/github/github-original.svg" width="16" height="16" alt="GitHub"/></a>
              <a href="{stats.get('linkedin_url', '#')}" target="_blank" rel="noopener noreferrer" aria-label="LinkedIn" style="display: inline-block; padding: 5px; background-color: #3f3f46; border-radius: 6px; margin-right: 5px; line-height: 0;"><img src="https://raw.githubusercontent.com/devicons/devicon/master/icons/linkedin/linkedin-plain.svg" width="16" height="16" alt="LinkedIn"/></a>
            </p>
          </td>
        </tr>
      </table>
    </td>
  </tr>
  <tr>
    <td align="center" style="border: 1px solid #3f3f46; background-color: #3a3a3a; border-radius: 10px; padding: 10px; margin: 5px;">
      <div style="color: #a3a3a3; font-size: 0.75rem; margin-bottom: 4px;">🏅 Problems Solved</div>
      <div style="color: #f5f5f5; font-size: 1.5rem; font-weight: bold;">{stats.get('solved', 'N/A')}</div>
    </td>
    <td align="center" style="border: 1px solid #3f3f46; background-color: #3a3a3a; border-radius: 10px; padding: 10px; margin: 5px;">
       <div style="color: #a3a3a3; font-size: 0.75rem; margin-bottom: 4px;">🔥 Current Streak</div>
       <div style="color: #f5f5f5; font-size: 1.5rem; font-weight: bold;">{streak_text}</div>
    </td>
  </tr>
  <tr>
    <td align="center" style="border: 1px solid #3f3f46; background-color: #3a3a3a; border-radius: 10px; padding: 10px; margin: 5px;">
      <div style="color: #a3a3a3; font-size: 0.75rem; margin-bottom: 4px;">⭐ Favorite Category</div>
      <div style="color: #f5f5f5; font-size: 0.875rem; font-weight: 500;">{stats.get('fav_category', 'N/A')}</div>
    </td>
    <td align="center" style="border: 1px solid #3f3f46; background-color: #3a3a3a; border-radius: 10px; padding: 10px; margin: 5px;">
       <div style="color: #a3a3a3; font-size: 0.75rem; margin-bottom: 4px;">💥 Score</div>
       <div style="color: #f5f5f5; font-size: 1.5rem; font-weight: bold;">{stats.get('score', 'N/A')}</div>
    </td>
  </tr>
</table>
"""
    pattern = re.compile(f"{re.escape(START_COMMENT)}(.*?){re.escape(END_COMMENT)}", re.DOTALL)
    # Important: Make sure START_COMMENT and END_COMMENT are exactly as in your README
    new_readme = pattern.sub(f"{START_COMMENT}\n{stats_table.strip()}\n{END_COMMENT}", readme_content) # Use strip() on table just in case
    return new_readme


# --- Main Execution Block ---
if __name__ == "__main__":
    print(f"Fetching stats from {PROFILE_URL} using Selenium with wait...")
    # Call the Selenium function
    current_stats = fetch_stats_with_wait(PROFILE_URL)

    if current_stats: # Check if we got a dictionary back
        # Check if we actually parsed something meaningful (e.g., username)
        if current_stats.get('username', 'N/A') != 'N/A' or current_stats.get('rank', 'N/A') != 'N/A':
             print("Successfully parsed some data.")
             try:
                 with open(README_PATH, 'r', encoding='utf-8') as f:
                     readme_content = f.read()

                 print("Generating updated README content...")
                 new_readme_content = generate_new_readme(current_stats, readme_content)

                 # Check if the generated content is different before writing
                 start_marker_index = readme_content.find(START_COMMENT)
                 end_marker_index = readme_content.find(END_COMMENT)
                 existing_block = ""
                 if start_marker_index != -1 and end_marker_index != -1:
                      existing_block = readme_content[start_marker_index:end_marker_index + len(END_COMMENT)]

                 new_block = f"{START_COMMENT}\n{generate_new_readme(current_stats, '').strip()}\n{END_COMMENT}" # Regenerate block cleanly

                 if new_readme_content != readme_content: # Compare full files first
                 # if existing_block != new_block: # Alternative: compare only the block
                     print(f"Updating {README_PATH}...")
                     with open(README_PATH, 'w', encoding='utf-8') as f:
                         f.write(new_readme_content)
                     print("README updated successfully.")
                 else:
                     print("No changes needed in README content.")

             except FileNotFoundError:
                 print(f"Error: {README_PATH} not found.")
             except Exception as e:
                 print(f"Error processing or writing README: {e}")
                 import traceback
                 print(traceback.format_exc())
        else:
             print("Could not parse significant data (username/rank still N/A). Skipping README update.")
    else:
        # This case means the fetch_stats function itself likely hit a major error and returned None (should be rare now)
        print("Fetching function failed to return stats. README update skipped.")