import re
import urllib.parse
import requests
from bs4 import BeautifulSoup
from alert import send_discord_alert
from downloader import download_syllabus_files
from pathlib import Path
# Static dictionary of department starting points
DEPARTMENT_URLS = {
    "COMPUTER_SCIENCE_AND_ENGINEERING": "https://vce.ac.in/departments/cse/cse-dept-cse-syllabus.php",
    "COMPUTER_SCIENCE_AND_ENGINEERING_(AI_&_ML)": "https://vce.ac.in/departments/cse/cse-dept-csm-syllabus.php",
    "ELECTRONICS_AND_COMMUNICATION_ENGINEERING": "https://vce.ac.in/departments/ece/ece-dept-syllabus.php",
    "ELECTRICAL_AND_ELECTRONICS_ENGINEERING": "https://vce.ac.in/departments/eee/eee-dept-syllabus.php",
    "INFORMATION_TECHNOLOGY": "https://vce.ac.in/departments/it/it-dept-syllabus.php",
    "MECHANICAL_ENGINEERING": "https://vce.ac.in/departments/mechanical/mech-dept-syllabus.php",
    "CIVIL_ENGINEERING": "https://vce.ac.in/departments/civil/civil-dept-syllabus.php"
}

def extract_syllabus_links(target_academic_year: str) -> dict:
    """
    STRICT EXTRACTOR: Scrapes college portal for syllabus PDFs.
    If ANY department is missing data, structurally changed, or fails to load,
    the entire process aborts and returns an empty dictionary {}.
    """

    print(f"[EXTRACTOR] Starting strict extraction for academic year: {target_academic_year}")
    
    extracted_dept_links = {}

    for dept, url in DEPARTMENT_URLS.items():
        print(f"[EXTRACTOR] Checking {dept}...")
        
        # --- CHECK 1: Network & Uptime ---
        try:
            response = requests.get(url, timeout=15)
            response.raise_for_status()
        except requests.RequestException as e:
            error_msg = (
                f"### 🚨**[LINK EXTRACTOR ERROR]** Phase 1 ABORTED: Network Error\n"
                f"- **Point of Failure:** `{dept}` Department Page\n"
                f"- **Details:** Failed to fetch URL. `{str(e)}`\n"
                f"- **Action:** Halting entire extraction. Site may be down."
            )
            print(f"[ERROR] {error_msg}")
            send_discord_alert(error_msg)
            return {}  # Abort entire run

        soup = BeautifulSoup(response.text, 'html.parser')

        # --- CHECK 2: Target Year Existence (Partial Upload Check) ---
        # Constrain the search to the accordion buttons to avoid matching inner syllabus text
        year_node = soup.find('button', class_='accordion-button', string=re.compile(target_academic_year))
        
        if not year_node:
            abort_msg = (
                f"### 🚨**[LINK EXTRACTOR ERROR]** Phase 1 ABORTED: Incomplete College Upload\n"
                f"- **Point of Failure:** `{dept}` Department\n"
                f"- **Details:** '{target_academic_year}' not found on this page.\n"
                f"- **Action:** Halting to prevent partial data collection. Waiting for college to upload all departments."
            )
            print(f"[INFO] {abort_msg}")
            send_discord_alert(abort_msg)
            return {}  # Abort entire run

        # --- CHECK 3: DOM Structure Integrity ---
        accordion_item = year_node.find_parent("div", class_="accordion-item")
        if not accordion_item:
            error_msg = (
                f"### 🚨**[LINK EXTRACTOR ERROR]** Phase 1 ABORTED: DOM Structure Change\n"
                f"- **Point of Failure:** `{dept}` Department\n"
                f"- **Details:** Found year '{target_academic_year}', but could not locate parent `.accordion-item`.\n"
                f"- **Action:** Manual intervention required. HTML structure likely changed."
            )
            print(f"[ERROR] {error_msg}")
            send_discord_alert(error_msg)
            return {}  # Abort entire run

        # --- CHECK 4: PDF Link Validation ---
        pdf_tags = accordion_item.select('a[href$=".pdf"]')
        if not pdf_tags:
            error_msg = (
                f"### 🚨**[LINK EXTRACTOR ERROR]** Phase 1 ABORTED: Missing PDF Data\n"
                f"- **Point of Failure:** `{dept}` Department\n"
                f"- **Details:** Accordion found for '{target_academic_year}', but no `.pdf` links inside.\n"
                f"- **Action:** Halting. Data is empty or incorrectly formatted on the site."
            )
            print(f"[ERROR] {error_msg}")
            send_discord_alert(error_msg)
            return {}  # Abort entire run

        # --- SUCCESS: Normalize and Store ---
        dept_links = []
        for tag in pdf_tags:
            relative_url = tag.get('href')
            absolute_url = urllib.parse.urljoin(url, relative_url)
            dept_links.append(absolute_url)

        extracted_dept_links[dept] = dept_links
        print(f"[SUCCESS] {dept}: Extracted {len(dept_links)} PDF links.")

    # If the loop finishes without returning {}, we have 100% complete data
    print(f"[SUCCESS] All departments successfully verified and extracted for {target_academic_year}.")
    return extracted_dept_links

# --- Quick Local Testing Block ---
if __name__ == "__main__":
    # Test with a known existing year to verify extraction logic
    target_year = "2025-2026"
    results = extract_syllabus_links(target_year)
    
    print("\n=== EXTRACTION RESULTS ===")
    for d, links in results.items():
        print(f"\n{d} ({len(links)} files):")
        for link in links:
            print(f" - {link}")

    success = download_syllabus_files(results)
    
    if success:
        print("Test passed: Files downloaded successfully.")
    else:
        print("Test failed: Downloader aborted.")