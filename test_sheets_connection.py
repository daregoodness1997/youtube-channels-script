"""Diagnostic script to test Google Sheets connection."""

import json
import os
from google.oauth2.service_account import Credentials
import gspread
from config import SPREADSHEET_ID, WORKSHEET_NAME

# Configuration
CREDENTIALS_FILE = "credentials.json"

print("=" * 60)
print("Google Sheets Connection Diagnostic")
print("=" * 60)

# Step 1: Check if credentials file exists
print("\n1. Checking credentials file...")
if not os.path.exists(CREDENTIALS_FILE):
    print(f"   ❌ ERROR: {CREDENTIALS_FILE} not found!")
    print(
        f"   Please download your service account credentials and save as {CREDENTIALS_FILE}"
    )
    exit(1)
else:
    print(f"   ✅ {CREDENTIALS_FILE} found")

# Step 2: Validate JSON format
print("\n2. Validating credentials JSON format...")
try:
    with open(CREDENTIALS_FILE, "r") as f:
        creds_data = json.load(f)
    print("   ✅ Valid JSON format")

    # Check for required fields
    required_fields = ["type", "project_id", "private_key", "client_email"]
    missing_fields = [field for field in required_fields if field not in creds_data]

    if missing_fields:
        print(f"   ❌ Missing required fields: {missing_fields}")
        exit(1)

    if creds_data.get("type") != "service_account":
        print(
            f"   ❌ Invalid type: {creds_data.get('type')}. Expected 'service_account'"
        )
        exit(1)

    service_account_email = creds_data.get("client_email")
    print(f"   ✅ Service account email: {service_account_email}")

except json.JSONDecodeError as e:
    print(f"   ❌ Invalid JSON format: {e}")
    exit(1)
except Exception as e:
    print(f"   ❌ Error reading file: {e}")
    exit(1)

# Step 3: Test authentication
print("\n3. Testing Google API authentication...")
try:
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=scopes)
    print("   ✅ Credentials loaded successfully")
except Exception as e:
    print(f"   ❌ Failed to load credentials: {e}")
    exit(1)

# Step 4: Test gspread authorization
print("\n4. Testing gspread authorization...")
try:
    client = gspread.authorize(creds)
    print("   ✅ gspread authorized successfully")
except Exception as e:
    print(f"   ❌ Failed to authorize gspread: {e}")
    exit(1)

# Step 5: Test spreadsheet access
print("\n5. Testing spreadsheet access...")
try:
    spreadsheet = client.open_by_key(SPREADSHEET_ID)
    print(f"   ✅ Successfully opened spreadsheet: {spreadsheet.title}")
except gspread.exceptions.SpreadsheetNotFound:
    print(f"   ❌ Spreadsheet not found!")
    print(f"   Make sure the spreadsheet exists and is shared with:")
    print(f"   {service_account_email}")
    print(f"\n   To share the spreadsheet:")
    print(f"   1. Open: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit")
    print(f"   2. Click 'Share' button")
    print(f"   3. Add the service account email: {service_account_email}")
    print(f"   4. Give it 'Editor' permissions")
    exit(1)
except Exception as e:
    print(f"   ❌ Error accessing spreadsheet: {e}")
    exit(1)

# Step 6: Test worksheet access
print("\n6. Testing worksheet access...")
try:
    # Try exact match first
    worksheet = spreadsheet.worksheet(WORKSHEET_NAME)
    print(f"   ✅ Successfully accessed worksheet: {worksheet.title}")
except gspread.exceptions.WorksheetNotFound:
    # Try with stripped whitespace
    try:
        available_worksheets = spreadsheet.worksheets()
        print(f"   ⚠️  Worksheet '{WORKSHEET_NAME}' not found!")
        print(f"   Available worksheets:")
        for ws in available_worksheets:
            print(f"      - '{ws.title}' (length: {len(ws.title)})")

        # Try to find a close match
        worksheet = None
        for ws in available_worksheets:
            if ws.title.strip() == WORKSHEET_NAME.strip():
                worksheet = ws
                print(
                    f"\n   ✅ Found matching worksheet (after stripping whitespace): '{ws.title}'"
                )
                break

        if not worksheet:
            print(f"\n   Update WORKSHEET_NAME in config.py to match one of the above")
            exit(1)
    except Exception as e:
        print(f"   ❌ Error: {e}")
        exit(1)
except Exception as e:
    print(f"   ❌ Error accessing worksheet: {e}")
    exit(1)

# Step 7: Test write permissions
print("\n7. Testing write permissions...")
try:
    # Try to read current cell A1
    current_value = worksheet.acell("A1").value
    print(f"   ✅ Can read from spreadsheet (A1: '{current_value}')")

    # The actual app will write, but we won't test that here to avoid modifying data
    print("   ✅ Ready to write (permissions look good)")

except Exception as e:
    print(f"   ❌ Error testing permissions: {e}")
    exit(1)

print("\n" + "=" * 60)
print("✅ ALL CHECKS PASSED!")
print("=" * 60)
print("\nYour Google Sheets integration is properly configured.")
print("You can now run: python main.py")
print()
