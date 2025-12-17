# Google Sheets Setup Guide

To enable Google Sheets integration, you need to set up a Google Cloud service account and download credentials.

## Step 1: Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google Sheets API:
   - Go to "APIs & Services" > "Library"
   - Search for "Google Sheets API"
   - Click "Enable"
4. Enable the Google Drive API:
   - Search for "Google Drive API"
   - Click "Enable"

## Step 2: Create Service Account

1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "Service Account"
3. Fill in the service account details:
   - Name: `youtube-data-api`
   - Description: `Service account for YouTube data API project`
4. Click "Create and Continue"
5. Skip the optional steps and click "Done"

## Step 3: Download Credentials

1. Click on the service account you just created
2. Go to the "Keys" tab
3. Click "Add Key" > "Create new key"
4. Select "JSON" format
5. Click "Create" - the credentials file will be downloaded
6. Rename the file to `credentials.json`
7. Move it to your project directory: `/Users/goodnessdare/Documents/youtube-data-api/credentials.json`

## Step 4: Share Your Spreadsheet

1. Open your Google Sheet: https://docs.google.com/spreadsheets/d/1I6-qS3scivhqyLTngCRX65JRh36rE1iulGNNWr97mec/edit
2. Click the "Share" button
3. Copy the service account email from the credentials.json file (it looks like: `youtube-data-api@your-project.iam.gserviceaccount.com`)
4. Paste it in the share dialog
5. Give it "Editor" permissions
6. Click "Send"

## Step 5: Update .gitignore

The `credentials.json` file is already added to `.gitignore` to prevent accidentally committing sensitive credentials.

## Step 6: Install Dependencies

```bash
source venv/bin/activate
pip install -r requirements.txt
```

## Step 7: Run the Application

```bash
python main.py
```

The application will now save data to both the SQLite database AND your Google Spreadsheet!

## Troubleshooting

- **Authentication Error**: Make sure you've shared the spreadsheet with the service account email
- **Permission Error**: Ensure the service account has "Editor" access to the spreadsheet
- **File Not Found**: Make sure `credentials.json` is in the project root directory
