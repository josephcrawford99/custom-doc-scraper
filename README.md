# Custom Documentation Scraper

This Python script scrapes lessons from a specified documentation website, converts them to Markdown, and saves them locally. It's designed to help users create an offline, organized version of online documentation.

## Features

*   Fetches web content using `requests`.
*   Parses HTML using `BeautifulSoup4`.
*   Converts HTML content to Markdown using `html2markdown`.
*   Extracts lesson links from a navigation sidebar or the main page content.
*   Handles relative and absolute URLs.
*   Organizes output files with numerical prefixes to maintain order.
*   Avoids saving duplicate content based on page titles.
*   Accepts the target URL and output directory as command-line arguments.

## Prerequisites

*   Python 3
*   pip (Python package installer)

## Setup

1.  **Clone the repository (or download the files):**
    ```bash
    git clone https://github.com/josephcrawford99/custom-doc-scraper.git
    cd custom-doc-scraper
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    (If you are on a system where `python3` is the command for Python 3, you might need to use `python3 -m pip install -r requirements.txt`)

## Usage

Run the script from your terminal, providing the base URL of the documentation website you want to scrape.

```bash
python scraper.py <URL_OF_DOCS_HOMEPAGE_OR_A_LESSON_PAGE>
```

**Examples:**

```bash
python scraper.py https://reactnative.dev/docs/getting-started
```

**Options:**

*   `URL`: (Required) The base URL of the documentation website to scrape (e.g., `https://reactnative.dev/docs/`).
*   `-o OUTPUT_DIR`, `--output OUTPUT_DIR`: (Optional) Directory to save markdown files. Defaults to `output_lessons`.
*   `-h`, `--help`: Show help message and exit.

Example with a custom output directory:
```bash
python scraper.py https://example.com/docs -o my_scraped_lessons
```

## How it Works

1.  The script starts by fetching the initial URL provided.
2.  It attempts to identify a "documentation base URL" to correctly resolve relative links and filter relevant content.
3.  It looks for lesson links primarily within navigation elements (e.g., a sidebar with class `sidebar_CUen` or a `nav` element with `aria-label="Docs sidebar"`).
4.  As a fallback, or in addition, it performs a broader search for all `<a>` tags on the page that seem to belong to the same documentation set.
5.  For each unique lesson link found:
    *   The page content is fetched.
    *   The main content area of the lesson is identified (currently targets `<article>`, then falls back to `<body>`).
    *   The HTML of this content area is converted to Markdown.
    *   A title is extracted from the page's `<title>` tag.
    *   The Markdown content is saved to a file, prefixed with a number to maintain order (e.g., `001_lesson-title.md`). Duplicate titles are skipped.

## Customization

The link extraction logic (in `extract_lesson_links`) and content scraping logic (in `scrape_lesson_content`) might need to be adjusted based on the specific HTML structure of the target website. Key areas to check:

*   **`extract_lesson_links` function:**
    *   The selectors used to find the navigation element (`soup.find('div', class_="sidebar_CUen")` and `soup.find('nav', attrs={"aria-label": "Docs sidebar"})`).
    *   The filtering logic for links.
*   **`scrape_lesson_content` function:**
    *   The selector for the main content area (`soup.find('article')`). If the target site doesn't use `<article>`, you might need to find a more suitable tag or class.

## Contributing

Feel free to fork this repository, make improvements, and submit pull requests.

## License

This project is open source and available under the [MIT License](LICENSE.md) (though a LICENSE.md file is not yet included in this repo).
