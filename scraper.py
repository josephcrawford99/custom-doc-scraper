#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
import html2markdown
import os
import re
import argparse
from urllib.parse import urlparse, urljoin


def fetch_url(url):
    """Fetches the content of a URL and returns a BeautifulSoup object."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Raise an exception for bad status codes
        return BeautifulSoup(response.content, "html.parser")
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None


def extract_lesson_links(soup, current_page_url, docs_base_url):
    """
    Extracts lesson links from the main documentation page.
    Uses current_page_url to resolve relative links and docs_base_url to filter.
    """
    links = []
    # Try a broader selector for the sidebar container first
    nav_element = soup.find("div", class_="sidebar_CUen")

    if not nav_element:
        # Fallback to the more specific nav element if the broader one isn't found
        print("Could not find sidebar_CUen div, trying specific nav element...")
        nav_element = soup.find("nav", attrs={"aria-label": "Docs sidebar"})

    if nav_element:
        for link_tag in nav_element.find_all("a", href=True):
            href = link_tag["href"]
            # Resolve the href to an absolute URL based on the current page's URL
            full_url = urljoin(current_page_url, href)
            # Remove any URL fragment
            full_url = urlparse(full_url)._replace(fragment="").geturl()

            # Add to links if it's within the docs_base_url, not already present, and not the base itself
            if (
                full_url.startswith(docs_base_url)
                and full_url not in links
                and full_url != docs_base_url
                and full_url != current_page_url
            ):
                links.append(full_url)
    else:
        # This message now means neither the broad div nor the specific nav was found.
        print(
            f"Could not find the primary navigation element on {current_page_url}. Searched for 'div.sidebar_CUen' and 'nav[aria-label=\"Docs sidebar\"]'."
        )
    return links


def scrape_lesson_content(soup):
    """
    Extracts the main content of a lesson page.
    This function will also likely need customization.
    """
    # Example: Find the main content area of the page
    # You'll need to inspect a lesson page on reactnative.dev/docs
    content_element = soup.find("article")  # This is a common tag for main content
    if content_element:
        return str(content_element)
    else:
        print("Could not find the main content element. Please check the selector.")
        return None


def convert_to_markdown(html_content):
    """Converts HTML content to Markdown."""
    if html_content:
        return html2markdown.convert(html_content)
    return ""


def save_markdown(markdown_content, filename, output_dir="output_lessons"):
    """Saves the Markdown content to a file."""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Sanitize filename
    sanitized_filename = re.sub(r'[\/*?:"<>|]', "", filename)
    # Ensure it ends with .md
    if not sanitized_filename.endswith(".md"):
        sanitized_filename += ".md"

    filepath = os.path.join(output_dir, sanitized_filename)
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(markdown_content)
        print(f"Saved: {filepath}")
    except IOError as e:
        print(f"Error saving {filepath}: {e}")


def get_lesson_title(soup, url):
    """Extracts a title from the page, or derives it from the URL."""
    if soup and soup.title and soup.title.string:
        return soup.title.string.strip()
    # Fallback to deriving from URL if title is not found
    try:
        # Get the last part of the URL path
        path_part = url.split("/")[-1] or url.split("/")[-2]
        # Remove .html or other extensions if present
        name_part = path_part.split(".")[0]
        # Replace hyphens/underscores with spaces and capitalize
        return name_part.replace("-", " ").replace("_", " ").title()
    except Exception:
        return "untitled_lesson"  # Default if all else fails


def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(
        description="Scrape lessons from a website and convert them to Markdown."
    )
    parser.add_argument(
        "url",
        help="The starting URL of the documentation website to scrape (e.g., https://reactnative.dev/docs/getting-started)",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="output_lessons",
        help="Directory to save markdown files (default: output_lessons)",
    )

    args = parser.parse_args()
    main_page_url = args.url
    output_dir = args.output

    # Derive docs_base_url (e.g., https://reactnative.dev/docs/)
    # This assumes the docs are in a path like /docs/, /guides/, etc.
    # For reactnative.dev/docs/getting-started, docs_base_url becomes https://reactnative.dev/docs/
    parsed_main_url = urlparse(main_page_url)
    path_segments = parsed_main_url.path.strip("/").split("/")
    if len(path_segments) > 1:  # e.g., 'docs', 'getting-started'
        docs_base_path = "/".join(path_segments[:-1]) + "/"
    else:  # e.g. just 'docs' or if it's the root
        docs_base_path = path_segments[0] + "/" if path_segments else ""

    docs_base_url = f"{parsed_main_url.scheme}://{parsed_main_url.netloc}/{docs_base_path.lstrip('/')}"

    print(f"Starting scrape with initial page: {main_page_url}")
    print(f"Derived documentation base URL: {docs_base_url}")

    main_soup = fetch_url(main_page_url)

    if not main_soup:
        print(
            f"Could not fetch the initial documentation page: {main_page_url}. Exiting."
        )
        return

    all_found_links = []

    # 1. Attempt targeted extraction from sidebar
    print("Attempting to extract links from known sidebar selectors...")
    sidebar_links = extract_lesson_links(main_soup, main_page_url, docs_base_url)
    if sidebar_links:
        print(f"Found {len(sidebar_links)} links using sidebar selectors.")
        all_found_links.extend(sidebar_links)
    else:
        print(
            f"No links found using specific sidebar selectors (tried 'div.sidebar_CUen' and 'nav[aria-label='Docs sidebar']')."
        )

    # 2. Always perform a broader search on the entire page for robustness
    print("Performing a broader search for links on the entire page...")
    page_wide_links = []
    for link_tag in main_soup.find_all("a", href=True):
        href = link_tag["href"]
        full_url = urljoin(main_page_url, href)
        full_url = urlparse(full_url)._replace(fragment="").geturl()

        if (
            full_url.startswith(docs_base_url)
            and full_url != main_page_url
            and full_url != docs_base_url
        ):
            page_wide_links.append(full_url)

    if page_wide_links:
        print(f"Found {len(page_wide_links)} links with page-wide search.")
        all_found_links.extend(page_wide_links)
    else:
        print(f"No additional links found with page-wide search on {main_page_url}.")

    # Deduplicate all collected links
    if not all_found_links:
        print(
            f"No lesson links found on {main_page_url} that match the criteria (within {docs_base_url})."
        )
        print(
            "Please check the website structure and ensure the starting URL is correct and contains links to other documentation pages."
        )
        return

    lesson_links = sorted(
        list(set(all_found_links))
    )  # Sort for consistent order before numbering

    print(
        f"Found {len(lesson_links)} unique lesson links to process after combining all methods."
    )
    if lesson_links:
        print(f"Sample links: {lesson_links[:min(5, len(lesson_links))]}")

    saved_page_titles = set()  # To track titles of already saved pages
    file_save_counter = 0  # Counter for actual files saved, used for filename prefix

    # Loop through all unique URLs found
    for idx, lesson_url in enumerate(lesson_links):
        print(f"Processing URL ({idx + 1}/{len(lesson_links)}): {lesson_url}")
        lesson_soup = fetch_url(lesson_url)
        if lesson_soup:
            lesson_title = get_lesson_title(lesson_soup, lesson_url)
            # print(f"  Extracted Title: {lesson_title}") # Optional: for debugging title extraction

            html_content = scrape_lesson_content(lesson_soup)
            if html_content:
                # Check if we've already saved a page with this exact title
                if lesson_title in saved_page_titles:
                    print(
                        f"  Skipping duplicate content for title: '{lesson_title}' (from URL: {lesson_url})"
                    )
                else:
                    markdown_content = convert_to_markdown(html_content)
                    if not markdown_content or not markdown_content.strip():
                        print(
                            f"  Skipping empty or whitespace-only markdown for title: '{lesson_title}' (from URL: {lesson_url})"
                        )
                    else:
                        file_save_counter += (
                            1  # Increment counter for successfully saved unique file
                        )
                        filename_base = (
                            lesson_title
                            if lesson_title != "untitled_lesson"
                            else lesson_url.split("/")[-1] or lesson_url.split("/")[-2]
                        )
                        sanitized_filename_base = re.sub(
                            r"[^a-zA-Z0-9_-]", "_", filename_base
                        )

                        numbered_filename = (
                            f"{file_save_counter:03d}_{sanitized_filename_base}"
                        )
                        save_markdown(markdown_content, numbered_filename, output_dir)
                        saved_page_titles.add(
                            lesson_title
                        )  # Add title to set after successful save
            else:
                print(f"  Could not scrape content from {lesson_url}")
        else:
            print(f"  Failed to fetch {lesson_url}")
        print("-" * 20)

    print(
        f"Scraping complete. {file_save_counter} unique lessons saved. Markdown files are in the '{output_dir}' directory."
    )


if __name__ == "__main__":
    main()
