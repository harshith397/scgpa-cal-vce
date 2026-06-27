import json
import urllib.request
import urllib.error
import os
# Discord webhook URL
DISCORD_WEBHOOK_URL =  os.getenv("DISCORD_WEBHOOK_URL")

def send_discord_alert(message: str, webhook_url: str = None) -> bool:
    """
    Sends a formatted markdown message to a specified Discord channel via Webhook.
    Uses built-in urllib to maintain zero external library dependencies.
    """
    target_url = webhook_url or DISCORD_WEBHOOK_URL
    
    if not target_url or target_url == "YOUR_DISCORD_WEBHOOK_URL_HERE":
        print("[ERROR] Discord webhook URL is not configured.")
        return False

    # Discord payload format. It expects a JSON object with a 'content' key.
    payload = {
        "content": message
    }
    
    # Encode the string payload into bytes
    data = json.dumps(payload).encode('utf-8')
    
    # Build the network request
    req = urllib.request.Request(
        target_url,
        data=data,
        headers={
            'User-Agent': 'Syllabus-Engine-Automation',
            'Content-Type': 'application/json'
        },
        method='POST'
    )

    try:
        # Fire the HTTP POST request
        with urllib.request.urlopen(req) as response:
            if response.status in (200, 204):
                print("[INFO] Notification successfully delivered to Discord.")
                return True
            else:
                print(f"[WARNING] Discord responded with unexpected status: {response.status}")
                return False
                
    except urllib.error.HTTPError as e:
        print(f"[ERROR] HTTP Error calling Discord webhook: {e.code} - {e.reason}")
        try:
            print(f"[ERROR] Response body: {e.read().decode('utf-8')}")
        except Exception:
            pass
        return False
    except urllib.error.URLError as e:
        print(f"[ERROR] Network/URL Error connecting to Discord: {e.reason}")
        return False

# --- Local Testing Block ---
if __name__ == "__main__":
    print("Testing Discord Alerting Component locally...")
    
    test_markdown_message = (
        "🚨 Syllabus Engine Test Alert\n"
        "- **Environment:** Local Desktop Development\n"
        "- **Status:** Component initialized successfully.\n"
        "*(This is a verification test for your reusable alerting layer)*"
    )
    
    send_discord_alert(test_markdown_message)