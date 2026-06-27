import os
import urllib.parse
import requests
from alert import send_discord_alert

def download_syllabus_files(syllabus_data: dict, base_dir: str = "syllabus_pdfs") -> bool:
    """
    STRICT DOWNLOADER: Takes a dictionary of PDF links and downloads them into subfolders.
    If ANY file fails to download or save, the entire process aborts and returns False.
    """
    if not syllabus_data:
        print("[DOWNLOADER] No data provided to download. Aborting.")
        return False

    print(f"\n[DOWNLOADER] Starting strict download phase to directory: ./{base_dir}/")

    # Ensure the master base directory exists
    try:
        os.makedirs(base_dir, exist_ok=True)
    except OSError as e:
        error_msg = f"### 🚨 Phase 2 ABORTED: System Error\nFailed to create master directory `{base_dir}`: `{str(e)}`"
        print(f"[ERROR] {error_msg}")
        send_discord_alert(error_msg)
        return False

    total_downloaded = 0

    for dept, urls in syllabus_data.items():
        print(f"[DOWNLOADER] Processing {dept} ({len(urls)} files)...")
        
        # Create department subfolder
        dept_dir = os.path.join(base_dir, dept)
        try:
            os.makedirs(dept_dir, exist_ok=True)
        except OSError as e:
            error_msg = f"### 🚨 Phase 2 ABORTED: System Error\nFailed to create directory for `{dept}`: `{str(e)}`"
            print(f"[ERROR] {error_msg}")
            send_discord_alert(error_msg)
            return False

        for url in urls:
            # Extract the actual filename from the URL (e.g., '01-syllabus-2025-26.pdf')
            parsed_url = urllib.parse.urlparse(url)
            filename = os.path.basename(parsed_url.path)
            
            # Fallback if URL structure is weird and has no clear filename
            if not filename.endswith(".pdf"):
                filename = f"fallback_{dept}_{total_downloaded}.pdf"
                
            filepath = os.path.join(dept_dir, filename)

            # --- CHECK: Network & Download ---
            try:
                # Using stream=True is a best practice for downloading files to prevent memory overload
                response = requests.get(url, stream=True, timeout=20)
                response.raise_for_status()
                
                # --- CHECK: File Write ---
                with open(filepath, 'wb') as file:
                    for chunk in response.iter_content(chunk_size=8192):
                        file.write(chunk)
                        
                total_downloaded += 1
                
            except requests.RequestException as e:
                error_msg = (
                    f"### 🚨 Phase 2 ABORTED: Network Error\n"
                    f"- **Point of Failure:** `{dept}` Department\n"
                    f"- **File:** `{filename}`\n"
                    f"- **URL:** `{url}`\n"
                    f"- **Details:** HTTP request failed. `{str(e)}`\n"
                    f"- **Action:** Halting entire download phase to prevent partial data."
                )
                print(f"[ERROR] {error_msg}")
                send_discord_alert(error_msg)
                return False
                
            except IOError as e:
                error_msg = (
                    f"### 🚨 Phase 2 ABORTED: File Write Error\n"
                    f"- **Point of Failure:** `{dept}` Department\n"
                    f"- **File:** `{filepath}`\n"
                    f"- **Details:** Disk write failed. `{str(e)}`\n"
                    f"- **Action:** Halting entire download phase."
                )
                print(f"[ERROR] {error_msg}")
                send_discord_alert(error_msg)
                return False

    # If the loops finish without returning False, all files are successfully on disk.
    print(f"[SUCCESS] Download Phase Complete. {total_downloaded} total files saved to ./{base_dir}/")
    return True

# --- Quick Local Testing Block ---
if __name__ == "__main__":
    # Mock data to test the folder creation and download logic safely
    # (Using a lightweight sample PDF for testing)
    mock_extracted_data = {
        "TEST_DEPT": [
            "https://vce.ac.in/departments/cse/downloads/syllabus/2023-24/01-syllabus-2023-24.pdf"
        ]
    }
    
    success = download_syllabus_files(mock_extracted_data, base_dir="test_downloads")
    
    if success:
        print("Test passed: Files downloaded successfully.")
    else:
        print("Test failed: Downloader aborted.")