import json
import sys
import os
from alert import send_discord_alert
from datetime import datetime
from pathlib import Path

def run_initial_state_check():
    
    # Path configuration for local testing
    SCRIPT_DIR = Path(__file__).resolve().parent
    REPO_ROOT = SCRIPT_DIR.parent
    STATE_FILE_PATH = REPO_ROOT / "public" / "state.json"
    
    # Ensure the state file exists for local development fallback
    if not os.path.exists(STATE_FILE_PATH):
        print(f"[CHECKER ERROR] State file not found at: {STATE_FILE_PATH}")
        send_discord_alert(f"🚨**[CHECKER ERROR]** State file not found at: {STATE_FILE_PATH}")
        print("Please create a 'state.json' file with initial values. Execution halted.")
        sys.exit(1)
        
    try:
        with open(STATE_FILE_PATH, 'r') as f:
            state_data = json.load(f)
    except json.JSONDecodeError:
        print(f"[CHECKER ERROR] Fail to parse JSON from {STATE_FILE_PATH}. Check file formatting.")
        send_discord_alert(f"🚨**[CHECKER ERROR]** Fail to parse JSON from {STATE_FILE_PATH}. Check file formatting.")
        return False

    target_academic_year = state_data.get("target_academic_year")
    if not target_academic_year:
        print("[CHECKER ERROR] 'target_academic_year' key missing in state.json.")
        send_discord_alert("🚨**[CHECKER ERROR]** 'target_academic_year' key missing in state.json.")
        return False

    # 2. Extract Years
    try:
        # Splits "20XX-20XY" and grabs the integer 20XX
        target_start_year = int(target_academic_year.split('-')[0])
    except (ValueError, IndexError):
        print(f"[CHECKER ERROR] Invalid target format: {target_academic_year}. Expected YYYY-YYYY.")
        send_discord_alert(f"🚨**[CHECKER ERROR]** Invalid target format: {target_academic_year}. Expected YYYY-YYYY.")
        return False

    current_system_year = 2025 #datetime.now().year

    print(f"[INFO] Target Engine Year: {target_start_year} | System Year: {current_system_year}")

    # 3. The Logic Routing
    # Case A: Target > Current (Already Completed)
    if target_start_year > current_system_year:
        print(f"[PROCESS] Engine is waiting for {target_start_year}. Current year ({current_system_year}) is already processed. Exiting cleanly.")
        return False

    # Case B: Target == Current (Time to Run)
    elif target_start_year == current_system_year:
        print("[PROCESS] Target year matches current year. Proceeding to web scraping phase...")
        return target_academic_year

    # Case C: Target < Current (State Lag / Failure)
    elif target_start_year < current_system_year:
        error_msg = (
            f"### 🚨**[CHECKER ERROR]** Syllabus Engine Fatal State Error\n"
            f"- **Issue:** Target year (`{target_start_year}`) is strictly less than System year (`{current_system_year}`).\n"
            f"- **Meaning:** The pipeline failed to increment the year during a previous execution, or the automation silently died.\n"
            f"- **Action Required:** Manual intervention needed. Check logs and update `state.json`."
        )
        print("[ERROR] State lag detected. Pushing alert to Discord...")
        send_discord_alert(error_msg)
        return False 


if __name__ == "__main__":
    run_initial_state_check()