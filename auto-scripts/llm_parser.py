import os
import json
import time
import base64
import sys
from groq import Groq
from alert import send_discord_alert
from dotenv import load_dotenv

load_dotenv()
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def validate_structure(data):
    if not isinstance(data, list): return False
    if not data: return True
        
    for block in data:
        if not isinstance(block, dict): return False
        if "PROGRAM" not in block or "DEPARTMENT" not in block or "SEMESTER" not in block or "SUBJECTS" not in block:
            return False
        if not isinstance(block["SUBJECTS"], dict): return False
        
    return True

def process_vision_data(INPUT_DIR: str = "extracted_tables" ,RATE_LIMIT_DELAY: int = 5) -> bool:
    """
    LLM ENGINE: Parses images to JSON. Implements API Key rotation on 429 limits.
    Returns True on total success, False on hard crash or total token exhaustion.
    """
    # 1. API Key Rotation Setup
    api_keys = [os.getenv("GROQ_API_KEY_1"), os.getenv("GROQ_API_KEY_2")]
    api_keys = [k for k in api_keys if k] # Filter out missing keys
    
    if not api_keys:
        error_msg = "### 🚨 Phase 4 ABORTED: Authentication Error\nNo Groq API keys found in environment variables."
        print(error_msg)
        send_discord_alert(error_msg)
        return None # Changed from False
        
    current_key_index = 0
    client = Groq(api_key=api_keys[current_key_index])
    print(f"[LLM PARSER] Initialized with Key {current_key_index + 1}. Total keys available: {len(api_keys)}")

    # 2. State Initialization
    master_data = {}

    completed_files = set()
    image_files = sorted([f for f in os.listdir(INPUT_DIR) if f.endswith('.png')])
    total_files = len(image_files)

    if total_files == 0:
        print("[LLM PARSER] No images found to process. Exiting cleanly.")
        return None

    # 3. Execution Loop
    for index, filename in enumerate(image_files, 1):
        if filename in completed_files:
            print(f"[{index}/{total_files}] Skipping {filename}... (Already parsed)")
            continue

        image_path = os.path.join(INPUT_DIR, filename)
        print(f"[{index}/{total_files}] Processing {filename}...")

        # Dynamic System Prompt injecting filename as fallback context
        system_prompt = f"""You are a strict data extraction parser. Extract academic syllabus details from the table in the image into a specific JSON object structure.

FALLBACK CONTEXT: If the image lacks explicit headers for the department or semester, use the filename '{filename}' as secondary context to deduce them. CRITICAL: The visual information inside the image ALWAYS takes absolute priority over the filename. Only use the filename if the image data is ambiguous. 

CONTEXTUAL FILTERING RULE: If the table represents non-academic schedules (sports, library, fees, hostel), ignore it and return an empty data array: {{"data": []}} 

STATIC MAPPING RULES (CRITICAL): 
1. PROGRAM: Must be strictly "B.E" or "M.E". 
2. DEPARTMENT: You must map any abbreviations to these exact strings ONLY: 
- "CIVIL ENGINEERING"(it may refered as Civil(case incensitive) in image ) 
- "COMPUTER SCIENCE AND ENGINEERING" (it may refered as cse(case incensitive) in image) 
- "COMPUTER SCIENCE AND ENGINEERING (AI & ML)"(it may refered as csm(case incensitive) in image) 
- "MECHANICAL ENGINEERING"(it may refered as mech(case incensitive) in image) 
- "ELECTRONICS AND COMMUNICATION ENGINEERING" (it may refered as ece(case incensitive) in image) 
- "ELECTRICAL AND ELECTRONICS ENGINEERING"(it may refered as eee(case incensitive) in image) 
- "INFORMATION TECHNOLOGY"(it may refered as it(case incensitive) in image) 
- SPECIALIZATION RULE: If the table is for an Honours degree or specialization (e.g., "Honours Degree in System on Chip Design"), the DEPARTMENT must remain the base department ONLY (e.g., "ELECTRONICS AND COMMUNICATION ENGINEERING"). However, you MUST append the specialization name to the end of EVERY SUBJECT NAME in that table separated by a hyphen. 

3. SEMESTER: MUST be exactly ONE of these strings: "1", "2", "3", "4", "5", "6", "7", or "8". 
- NO RANGES OR TEXT: You are STRICTLY FORBIDDEN from returning values like "5 to 7", "1-2", "V", or "Sem 1". 
- SPANNING SEMESTERS: If a table or row spans multiple semesters (e.g., "V to VII" or "5 to 7"), you MUST split this range into individual semesters (e.g., "5", "6", "7"). For EACH semester in that range, create a completely separate, duplicate object inside the "data" array containing that semester's individual integer string and the exact same subjects. Do NOT output ranges like "5 to 7" as the SEMESTER value. 
- MULTIPLE DISTINCT SEMESTERS: If a table lists different semesters row-by-row, group them and create a separate object in the JSON array for EACH distinct semester. 

4. CREDITS: If blank or '-', output "0". 

OUTPUT SCHEMA FORMAT: You MUST return a JSON object with a single root key called "data". The value of "data" must be an array of objects. 
{{ 
  "data": [ 
    {{ 
      "PROGRAM": "B.E", 
      "DEPARTMENT": "CIVIL ENGINEERING", 
      "SEMESTER": "1", 
      "SUBJECTS": {{ 
        "SUBJECT NAME IN UPPERCASE": {{ 
          "COURSE CODE": "string", 
          "CREDITS": "string" 
        }} 
      }} 
    }} 
  ] 
}} 

Return ONLY valid JSON matching this exact schema. No markdown formatting blocks, no explanations."""


        retry_count = 0
        max_retries = 3
        processing_complete = False

        while not processing_complete:
            try:
                base64_image = encode_image(image_path)
                
                response = client.chat.completions.create(
                    model="meta-llama/llama-4-scout-17b-16e-instruct",
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": system_prompt},
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/png;base64,{base64_image}"
                                    }
                                }
                            ]
                        }
                    ],
                    temperature=0.0, # Lock to deterministic logic
                    response_format={"type": "json_object"}, 
                    max_completion_tokens=3048
                )
                
                raw_output = response.choices[0].message.content.strip()
                extracted_json = json.loads(raw_output)
                
                # --- DATA NORMALIZATION PEELER ---
                data_list = []
                if isinstance(extracted_json, dict):
                    if "data" in extracted_json and isinstance(extracted_json["data"], list):
                        data_list = extracted_json["data"]
                    else:
                        for key, value in extracted_json.items():
                            if isinstance(value, list):
                                data_list = value
                                break
                
                # --- SCHEMA VALIDATION ---
                if not validate_structure(data_list):
                    error_msg = (
                        f"### 🚨 Phase 4 ABORTED: Structural Hallucination\n"
                        f"- **File:** `{filename}`\n"
                        f"- **Details:** Model returned invalid JSON schema. Execution halted."
                    )
                    print(error_msg)
                    send_discord_alert(error_msg)
                    return False
                
                # --- DATA INJECTION ---
                # --- DATA INJECTION ---
                if data_list:
                    for block in data_list:
                        prog = block["PROGRAM"]
                        dept = block["DEPARTMENT"]
                        sem = block["SEMESTER"]
                        subs = block["SUBJECTS"]

                        if prog not in master_data: master_data[prog] = {}
                        if dept not in master_data[prog]: master_data[prog][dept] = {}
                        if sem not in master_data[prog][dept]: master_data[prog][dept][sem] = {}

                        for sub_name, sub_details in subs.items():
                            master_data[prog][dept][sem][sub_name] = sub_details

                completed_files.add(filename)
                processing_complete = True
                print(f"  -> Success. Data merged in memory.")
                
                time.sleep(RATE_LIMIT_DELAY)
                
            except Exception as e:
                error_str = str(e)
                
                # --- 429 RATE LIMIT HANDLING & ROTATION ---
                if "429" in error_str:
                    print(f"  -> [WARNING] Rate limit (429) hit on Key {current_key_index + 1}.")
                    
                    # Attempt Rotation
                    if current_key_index < len(api_keys) - 1:
                        current_key_index += 1
                        print(f"  -> [ROTATION] Switching to Key {current_key_index + 1}...")
                        client = Groq(api_key=api_keys[current_key_index])
                        time.sleep(5) 
                        continue
                    else:
                        error_msg = "### 🚨 Phase 4 ABORTED: Exhausted API Limits\nAll provided Groq keys hit 429 limits. Process halted. Progress has been saved."
                        print(error_msg)
                        send_discord_alert(error_msg)
                        return False
                
                # --- STANDARD ERROR RETRY LOGIC ---
                else:
                    retry_count += 1
                    if retry_count <= max_retries:
                        print(f"  -> ERROR on {filename}: {e}\n  -> Retrying in 5 seconds...")
                        time.sleep(5)
                    else:
                        error_msg = f"### 🚨 Phase 4 ABORTED: API Exception\nPersistent error on `{filename}` after {max_retries} retries: `{error_str}`"
                        print(error_msg)
                        send_discord_alert(error_msg)
                        return False

    # 4. Final Success Alert
    success_msg = (
        f"### ✅ Phase 4 Completed: LLM Compilation Engine\n"
        f"- **Images Parsed:** {total_files}\n"
        f"- **Status:** Proceeding to final verification."
    )
    print(success_msg)
    send_discord_alert(success_msg)
    return master_data

if __name__ == "__main__":
    process_vision_data()