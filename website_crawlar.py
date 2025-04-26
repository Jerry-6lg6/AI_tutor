import requests
import random
import time
import json
import re
import os
import tqdm
from bs4 import BeautifulSoup

# List of User-Agents to avoid detection
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/109.0",
    "Mozilla/5.0 (Linux; Android 10; Pixel 4 XL) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/537.36 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/537.36",
    "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
]


# Function to get random headers
def get_random_headers():
    return {"User-Agent": random.choice(USER_AGENTS)}


def sanitize_filename(filename):
    # Replace any invalid characters for a Windows path (such as /, \, :, *, ?, ", <, >, |)
    invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
    for char in invalid_chars:
        filename = filename.replace(char, '_')  # You can use any other character, like '_'
    return filename


def scrape_sql_page(url="https://www.w3schools.com/sql/", title="Default Title", key='sql', root=''):
    title = sanitize_filename(title)
    output_file = f"{title}.json"

    session = requests.Session()  # Use session to maintain cookies
    retries = 3  # Number of retries
    folder_path = os.path.join(root, key)  # Folder to save the content in

    for _ in range(retries):
        try:
            # Send request with random User-Agent
            response = session.get(url, headers=get_random_headers(), timeout=10)

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")
                content = []

                # Find all <h2> tags (main sections)
                for h2 in soup.find_all("h2"):
                    if h2.get("class") or h2.find(True):  # `h2.get("class")` 检查 class 属性，`h2.find(True)` 检查是否有任何子标签
                        continue

                    if re.search(r"Video|Contact Sales|Report Error", h2.text.strip()):
                        break

                    section = {"title": h2.text.strip(), "text": [], "examples": [], "tables": []}

                    next_tag = h2.find_next_sibling()
                    if next_tag and next_tag.name == 'a':  # Check if next_tag is valid and is an 'a' tag
                        continue

                    while next_tag and next_tag.name != "h2":  # Proceed until the next <h2> tag
                        print(f'this tag is {h2.text.strip()}, the next of it is {next_tag.name}')

                        try:
                            if next_tag.name == "p":
                                section["text"].append(next_tag.text.strip())

                            if next_tag.name == 'div' and next_tag.find_next_sibling():
                                if next_tag.find_next_sibling().name != "h3":
                                    section["text"].append(next_tag.text.strip())

                            # Extract SQL examples **with their associated <h3> headings**
                            if next_tag.name == "div" and any(
                                    re.compile(r"example").search(cls) for cls in next_tag.get("class", [])):
                                h3_tag = next_tag.find("h3")
                                sql_code_div = next_tag.find("div", class_="w3-code")

                                if h3_tag and sql_code_div:
                                    section["examples"].append({
                                        "heading": h3_tag.text.strip(),
                                        "code": sql_code_div.text.strip()
                                    })

                            # Extract tables
                            if next_tag.name == "div" and "w3-responsive" in next_tag.get("class", []):
                                table = next_tag.find("table")
                                if table:
                                    headers = [th.text.strip() for th in table.find_all("th")]
                                    rows = []
                                    for row in table.find_all("tr")[1:]:  # Skip the header row
                                        cells = [td.text.strip() for td in row.find_all("td")]
                                        rows.append(dict(zip(headers, cells)))

                                    section["tables"].append(rows)

                        except Exception as e:
                            print(f"Error while processing tag {next_tag}: {e}")
                            # Skip this tag and continue with the next one
                            next_tag = next_tag.find_next_sibling()
                            continue  # Skip current iteration and go to the next tag

                        next_tag = next_tag.find_next_sibling()

                    content.append(section)

                # Ensure the directory exists
                if not os.path.exists(folder_path):
                    os.makedirs(folder_path)

                # Save to JSON file
                file_path = os.path.join(folder_path, output_file)
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(content, f, indent=4, ensure_ascii=False)

                return content  # Return structured data if successful

            else:
                print(f"Failed to fetch page. Status Code: {response.status_code}")

        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")

        except Exception as e:
            print(f"Unexpected error occurred: {e}")

        # Introduce a random delay to avoid detection
        time.sleep(random.uniform(1, 3))

    return None  # Return None if all retries fail


# Example usage:
# url = "https://www.w3schools.com/sql/sql_and.asp"
# url1 = 'https://www.w3schools.com/java/java_variables.asp'
# scraped_data = scrape_sql_page(url)
#
# # Save to JSON file
# if scraped_data:
#     with open("sql_data.json", "w", encoding="utf-8") as f:
#         json.dump(scraped_data, f, indent=4, ensure_ascii=False)
#
#     print(json.dumps(scraped_data, indent=4, ensure_ascii=False))  # Print the result
# else:
#     print("Scraping failed!")


def scrape_sql_info(url="https://www.w3schools.com/sql/", title="Default Title"):
    """
    Scrapes SQL-related content from W3Schools and saves it as a JSON file.

    :param title:
    :param url: The URL of the W3Schools SQL page.
    :param output_file: The name of the output JSON file.
    """

    output_file = f"{title}.json"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")
        sql_data = []

        # Find all sections separated by <hr>
        sections = soup.find_all("hr")

        for section in sections:
            # Extract heading
            next_heading = section.find_next("h2")
            if next_heading:
                topic = {"title": next_heading.text.strip(), "content": []}

                # Extract paragraphs under each heading
                for p in next_heading.find_all_next("p", limit=5):
                    topic["content"].append({"type": "text", "value": p.text.strip()})

                # Extract lists under each heading
                next_list = next_heading.find_next("ul")
                if next_list:
                    list_items = [li.text.strip() for li in next_list.find_all("li")]
                    topic["content"].append({"type": "list", "value": list_items})

                sql_data.append(topic)

        # Save to JSON file
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(sql_data, f, indent=4, ensure_ascii=False)

        print(f"Data successfully saved to {output_file}")
        return sql_data

    else:
        print("Failed to fetch page")
        return None


def scrape_sql_links(key='sql'):
    """
    Scrapes all SQL tutorial links from the sidebar on W3Schools,
    excluding the 'SQL Examples' section, and saves them in a JSON file.

    :param url: The URL of the W3Schools SQL page.
    :param output_file: The name of the output JSON file.
    """
    url = fr"https://www.w3schools.com/{key}/"

    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    output_file = fr"{key}_links.json"
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")
        sql_links = []

        # Locate the sidebar
        sidebar = soup.find("div", id="leftmenuinnerinner")

        if sidebar:
            # Locate all <h2> elements with class "left"
            sections = sidebar.find_all("h2", class_="left")

            for section in sections:
                # Exclude the "SQL Examples" section
                if "Examples" in section.text:
                    continue

                # Find all links (<a>) under this section
                for link in section.find_all_next("a", href=True):
                    href = link["href"]
                    text = link.text.strip()

                    # Stop if we reach another <h2> (next section starts)
                    if link.find_previous("h2") != section:
                        break

                    if href.startswith(f"{key}_"):  # Ensuring SQL tutorial links only
                        full_url = f"https://www.w3schools.com/{key}/{href}"
                        sql_links.append({"title": text, "url": full_url})

        # 指定文件夹路径
        folder_path = f"{key}_folder"  # 目标文件夹

        file_path = os.path.join(folder_path, output_file)  # 组合完整路径

        # 如果目标文件夹不存在，则创建
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        # Save to JSON file
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(sql_links, f, indent=4, ensure_ascii=False)

        print(f"Data successfully saved to {output_file}")
        return sql_links

    else:
        print("Failed to fetch page")
        return None


# with open('sql_links.json', 'r') as file:
#     link_list = json.load(file)
# print(link_list)
# for item in link_list:
#     url = item['url']
#     print(url)
#     scrape_sql_page(url, item['title'])
folder_path = 'data'
# Loop through the directory
for root, dirs, files in os.walk(folder_path):

    # Find files that contain '_links.json'
    links_files = [f for f in files if '_links.json' in f]
    if links_files:
        for link_file in links_files:
            # You can add further logic to process these files
            result = link_file.split('_links')[0]
            full_file_path = os.path.join(root, link_file)
            with open(full_file_path, 'r', encoding='utf-8') as file:
                link_list = json.load(file)
            for item in link_list:
                url = item['url']
                print(url)
                scrape_sql_page(url, item['title'], result, root)

        # Uncomment and define the function to scrape URLs
        # scrape_sql_page(url, item['title'])

    print('-' * 40)
# Example usage
# sql_tutorial_links = scrape_sql_links('xml')

# # Example usage
#
# scraped_data = scrape_sql_info()
