import requests
from bs4 import BeautifulSoup
import re
import os

# --- Configuration ---
PROFILE_URL = "https://www.deep-ml.com/profile/Y5llgZoBWpPVmkyEw0guauFb8IG2" # Your Deep-ML profile URL
README_PATH = r"_tabs/about.md"

START_COMMENT = "<!-- START_DEEPML_STATS -->"
END_COMMENT = "<!-- END_DEEPML_STATS -->"
# --- End Configuration ---

def fetch_stats(url):
    """Fetches and parses stats from the Deep-ML profile page."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
        soup = BeautifulSoup(response.text, 'html.parser')

        stats = {
            "rank": "168",
            "solved": "68",
            "streak": "3",
            "fav_category": "Machine Learning",
            "score": "930",
            "avatar_url": "", # Add default empty string
            "username": "Jakcrimson",
            "email": "pierre.lague@protonmail.com",
            "github_url": "https://github.com/Jakcrimson",
            "linkedin_url": "https://www.linkedin.com/in/pierre-lague-479344195/",
        }

        # --- Parsing Logic (IMPORTANT: This might break if deep-ml.com changes layout) ---

        # Find the main profile div
        profile_div = soup.find('div', class_='lg:col-span-1')
        if not profile_div:
             print("Error: Could not find main profile container div.")
             return None # Or return default stats

        # Extract basic info
        avatar_img = profile_div.find('img', alt='Jakcrimson') # Use the alt text you expect
        stats['avatar_url'] = avatar_img['src'] if avatar_img else 'DEFAULT_AVATAR_URL' # Provide a default

        username_h2 = profile_div.find('h2', class_='text-xl')
        stats['username'] = username_h2.text.strip() if username_h2 else 'Your Username'

        email_p = profile_div.find('p', class_='text-sm text-zinc-400')
        stats['email'] = email_p.text.strip() if email_p else 'your.email@example.com'

        # Extract Rank
        rank_div = profile_div.find('div', class_='flex items-center mt-1')
        if rank_div:
             rank_text = rank_div.find('span')
             if rank_text:
                  match = re.search(r'Rank #(\d+)', rank_text.text)
                  if match:
                      stats['rank'] = match.group(1)

        # Extract Social Links (assuming specific aria-labels)
        github_a = profile_div.find('a', {'aria-label': 'GitHub'})
        stats['github_url'] = github_a['href'] if github_a else '#'
        linkedin_a = profile_div.find('a', {'aria-label': 'LinkedIn'})
        stats['linkedin_url'] = linkedin_a['href'] if linkedin_a else '#'


        # Extract Stats from grid
        stats_grid = profile_div.find('div', class_='grid grid-cols-2 gap-3')
        if stats_grid:
            stat_items = stats_grid.find_all('div', recursive=False) # Find direct children divs
            for item in stat_items:
                h3 = item.find('h3')
                if h3:
                    h3_text = h3.text.strip()
                    p = item.find('p', class_='text-2xl') # For solved, streak
                    p_sm = item.find('p', class_='text-sm') # For category
                    p_lg = item.find('p', class_='text-lg') # For score

                    if "Problems Solved" in h3_text and p:
                        stats['solved'] = p.text.strip()
                    elif "Current Streak" in h3_text and p:
                        # Extract number from "X days"
                        match = re.search(r'(\d+)\s+days', p.text)
                        stats['streak'] = match.group(1) if match else '0'
                    elif "Favorite Category" in h3_text and p_sm:
                        stats['fav_category'] = p_sm.text.strip()
                    elif "Flame Score" in h3_text and p_lg: # Assuming score is in text-lg p
                         stats['score'] = p_lg.text.strip()
                    # Need to adjust if the Score H3 text or P class is different
                    elif item.find('img', alt='Flame'): # Alternative way to find score if Flame Score H3 changed
                        score_p = item.find('p', class_='text-lg font-bold text-white')
                        if score_p:
                            stats['score'] = score_p.text.strip()

        print("Fetched Stats:", stats) # For debugging
        return stats

    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL {url}: {e}")
        return None
    except Exception as e:
        print(f"Error parsing HTML: {e}")
        return None


def generate_new_readme(stats, readme_content):
    """Generates the new README content with updated stats."""
    if not stats:
        print("No stats fetched, README will not be updated.")
        return readme_content # Return original content if stats fetching failed

    # Format the streak correctly
    streak_text = f"{stats.get('streak', '0')} days"

    # Build the new stats table HTML
    # Important: Keep this structure consistent with your README placeholders
    stats_table = f"""
<table align="center" width="350px" style="border: 1px solid #404040; border-radius: 12px; background-color: #262626; padding: 15px;">
  <tr>
    <td colspan="2">
      <table width="100%">
        <tr>
          <td width="70px" valign="top">
            <img src="{stats.get('avatar_url', '')}" alt="{stats.get('username', 'User')}" width="64" height="64" style="border-radius: 50%; border: 2px solid #525252;" />
          </td>
          <td valign="top" style="padding-left: 10px;">
            <h2 style="margin: 0; color: #f5f5f5; font-size: 1.25rem; font-weight: 500;">{stats.get('username', 'Username')}</h2>
            <p style="margin: 0; font-size: 0.875rem; color: #a3a3a3;">{stats.get('email', '')}</p>
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

    # Use regex to find and replace the content between the comments
    pattern = re.compile(f"{re.escape(START_COMMENT)}(.*?){re.escape(END_COMMENT)}", re.DOTALL)
    new_readme = pattern.sub(f"{START_COMMENT}\n{stats_table}\n{END_COMMENT}", readme_content)

    if new_readme == readme_content:
         print("No change detected in the stats section.")

    return new_readme

if __name__ == "__main__":
    print(f"Fetching stats from {PROFILE_URL}...")
    current_stats = fetch_stats(PROFILE_URL)

    if current_stats:
        try:
            with open(README_PATH, 'r', encoding='utf-8') as f:
                readme_content = f.read()

            print("Generating updated README content...")
            new_readme_content = generate_new_readme(current_stats, readme_content)

            if new_readme_content != readme_content:
                print(f"Updating {README_PATH}...")
                with open(README_PATH, 'w', encoding='utf-8') as f:
                    f.write(new_readme_content)
                print("README updated successfully.")
            else:
                print("No changes needed in README.")

        except FileNotFoundError:
            print(f"Error: {README_PATH} not found.")
        except Exception as e:
            print(f"Error writing to README: {e}")
    else:
        print("Could not fetch stats. README update skipped.")