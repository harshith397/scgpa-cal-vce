import subprocess
import sys
from checker import run_initial_state_check
from links_extractor import extract_syllabus_links
from downloader import download_syllabus_files
from image_extractor import extract_scheme_pages
from alert import send_discord_alert
from llm_parser import process_vision_data
from verify import verify_syllabus_structure
from pathlib import Path
import json
import re


def update_files_before_commit(target_dict_data):
    """Writes dictionary to JSON and increments academic year. Returns boolean status."""
    try:
        # File 1: Write target data
        prod_json_path = Path("src") / "data" / "syllabus.json"
        prod_json_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(prod_json_path, 'w', encoding='utf-8') as f:
            json.dump(target_dict_data, f, indent=2)

        # File 2: Increment Academic Year
        year_file_path = Path("public") / "state.json"
        
        # Safety check: Ensure the file exists before trying to read it
        if not year_file_path.exists():
            send_discord_alert(f"🚨 **File Missing**: Cannot find `{year_file_path}` to update academic year.")
            return False

        with open(year_file_path, 'r', encoding='utf-8') as f:
            year_data = json.load(f)
        
        # Safety check: Validate the key and format exist
        current_year = year_data.get("target_academic_year")
        if not current_year or '-' not in current_year:
            send_discord_alert(f"🚨 **Data Error**: Invalid or missing `target_academic_year` format in data.json: {current_year}")
            return False

        start_year, end_year = current_year.split('-')
        year_data["target_academic_year"] = f"{int(start_year) + 1}-{int(end_year) + 1}"

        with open(year_file_path, 'w', encoding='utf-8') as f:
            json.dump(year_data, f, indent=2)
            
        return True

    except json.JSONDecodeError as e:
        send_discord_alert(f"🚨 **JSON Error**: Failed to parse data.json.\nDetails: `{str(e)}`")
        return False
    except Exception as e:
        # Catch any unexpected OS, Permission, or IO errors
        send_discord_alert(f"🚨 **File System Error**: Exception during file operations.\nDetails: `{str(e)}`")
        return False
    

def run_git_command(command):
    """Executes a git command. Alerts Discord and returns False if it fails."""
    try:
        result = subprocess.run(
            command, 
            check=True, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True
        )
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        error_msg = f"Git command failed: {' '.join(command)}\nError: {e.stderr}"
        print(error_msg, file=sys.stderr)
        # Limit stderr length in discord alert to avoid message size limits
        send_discord_alert(f"🚨 **Git Error**\nCommand: `{' '.join(command)}`\nDetails: `{e.stderr[:300]}`")
        return False

def push_to_github():
    """Handles Git staging, committing, and pushing. Returns boolean success status."""
    print("Initiating Git sequence...")
    
    # 1. Config
    if not run_git_command(['git', 'config', '--global', 'user.name', 'github-actions[bot]']): return False
    if not run_git_command(['git', 'config', '--global', 'user.email', 'github-actions[bot]@users.noreply.github.com']): return False
    
    # 2. Stage files
    sate_file_path = (Path("public") / "state.json").as_posix()
    syllabus_file_path = (Path("src") / "data" / "syllabus.json").as_posix()
    
    if not run_git_command(['git', 'add', sate_file_path, syllabus_file_path]): return False
    
    # 3. Check for actual changes
    diff = subprocess.run(['git', 'diff', '--staged', '--quiet'])
    if diff.returncode == 0:
        print("No changes detected in the target files. Skipping commit.")
        send_discord_alert("✅**Pipeline Completed**: No new data to push.")
        return True # Returning True because this isn't a failure, just a no-op

    # 4. Commit and Push
    if not run_git_command(['git', 'commit', '-m', 'chore: update production JSON data and academic year']): return False
    if not run_git_command(['git', 'push']): return False
    
    return True

def main():
    # Step 1: Execute your sequential logic
    print("Starting data pipeline...")
    
    target_year=run_initial_state_check()
    if not target_year:
        send_discord_alert("🚨**[TRIGGER ABORTED]** Trigger Execution is aborted due to checker.py exectution")
        return 
    
    extracted_dept_links=extract_syllabus_links(target_year)
    if not extracted_dept_links:
        send_discord_alert("🚨**[TRIGGER ABORTED]** Trigger Execution is aborted due to links_extracter.py exectution")
        return 
    
    download_res=download_syllabus_files(extracted_dept_links)
    if not download_res:
        send_discord_alert("🚨**[TRIGGER ABORTED]** Trigger Execution is aborted due to downloader.py exectution")
        return 
    
    schema_pages_res=extract_scheme_pages()
    if not schema_pages_res:
       send_discord_alert("🚨**[TRIGGER ABORTED]** Trigger Execution is aborted due to image_extractor.py exectution")
       return 
    
    syl_data=process_vision_data()
    if not syl_data:
        send_discord_alert("🚨**[TRIGGER ABORTED]** Trigger Execution is aborted due to llm_parser.py exectution")
        return 
    
    verification=verify_syllabus_structure(syl_data)
    
    if not verification:
        send_discord_alert("🚨**[TRIGGER ABORTED]** Trigger Execution is aborted due to verification.py exectution")
        return
    
    send_discord_alert("✅ **Pipeline Success**: JSON data and academic year updated and pushed to production.")
    

    files_updated_successfully = update_files_before_commit(syl_data)
    
    if not files_updated_successfully:
        print("File update failed. Aborting Git sequence.", file=sys.stderr)
        return 

    push_success = push_to_github()
        
    # 6. Final Acknowledgment
    if push_success:
        send_discord_alert("✅ **Pipeline Success**: JSON data and academic year updated and pushed to production.")
    else:
        send_discord_alert("🚨 **Pipeline Failed**: JSON data and academic year not updated and pushed to production.")
   
if __name__ == "__main__":
    main()