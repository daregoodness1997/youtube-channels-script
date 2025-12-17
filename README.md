# YouTube Data API Project

A modular Python application for fetching YouTube channel statistics and storing them in a SQLite database and Google Sheets.

## Project Structure

```
youtube-data-api/
├── main.py                  # Main entry point
├── config.py                # Configuration settings
├── database.py              # Database operations
├── youtube_api.py           # YouTube API interactions
├── google_sheets.py         # Google Sheets integration
├── requirements.txt         # Python dependencies
├── credentials.json         # Google service account credentials (not in repo)
├── README.md                # This file
└── GOOGLE_SHEETS_SETUP.md   # Google Sheets setup instructions
```

## Features

✅ Fetch all videos from a YouTube channel
✅ Retrieve video statistics (views, likes, comments)
✅ Store data in SQLite database
✅ Export data to Google Sheets automatically
✅ Batch processing for efficient API usage
✅ Modular and extensible codebase

## Setup Instructions

### 1. Create Virtual Environment

```bash
python3 -m venv venv
```

### 2. Activate Virtual Environment

**macOS/Linux:**
```bash
source venv/bin/activate
```

**Windows:**
```bash
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure YouTube API Key

Edit `config.py` and add your YouTube Data API key:

```python
API_KEY = "your_youtube_api_key_here"
```

### 5. Set Up Google Sheets (Optional but Recommended)

Follow the detailed instructions in [GOOGLE_SHEETS_SETUP.md](GOOGLE_SHEETS_SETUP.md) to:
- Create a Google Cloud service account
- Download credentials
- Share your spreadsheet with the service account

**Your spreadsheet**: https://docs.google.com/spreadsheets/d/1I6-qS3scivhqyLTngCRX65JRh36rE1iulGNNWr97mec/edit

If you skip this step, the application will still work but only save to the local database.

## Usage

### Quick Start (CLI)

**Extract data from a channel:**

```bash
./youtube-data https://www.youtube.com/@channelname
```

**Extract data from a single video:**

```bash
./youtube-data https://www.youtube.com/watch?v=dQw4w9WgXcQ
```

Or with just IDs:

```bash
# Channel
./youtube-data UCPix8N6PMRI4KzgyjuZeF0g

# Video
./youtube-data dQw4w9WgXcQ
```

### Command Line Options

**Channel Examples:**
```bash
# Using channel URL
python main.py https://www.youtube.com/@channelname

# Using channel ID
python main.py UCPix8N6PMRI4KzgyjuZeF0g

# Using handle
python main.py @channelname
```

**Video Examples:**
```bash
# Using video URL
python main.py https://www.youtube.com/watch?v=dQw4w9WgXcQ

# Using short URL
python main.py https://youtu.be/dQw4w9WgXcQ

# Using video ID
python main.py dQw4w9WgXcQ
```

**Options:**
```bash
# Interactive mode (will prompt for input)
python main.py

# Skip Google Sheets export (database only)
python main.py UCPix8N6PMRI4KzgyjuZeF0g --no-sheets

# Skip transcripts for faster processing
python main.py UCPix8N6PMRI4KzgyjuZeF0g --no-transcripts
```

### Supported Input Formats

**Channels:**

- **Channel ID**: `UCPix8N6PMRI4KzgyjuZeF0g`
- **Channel URL**: `https://www.youtube.com/channel/UCPix8N6PMRI4KzgyjuZeF0g`
- **Handle**: `@channelname` or `https://www.youtube.com/@channelname`
- **Username**: `username` or `https://www.youtube.com/user/username`
- **Custom URL**: `https://www.youtube.com/c/channelname`

### What it Does

The script will:
1. Fetch all videos from the specified YouTube channel
2. Retrieve statistics (views, likes, comments) for each video
3. Store the data in `youtube_data.db` SQLite database
4. Export the data to your Google Spreadsheet (if configured)

## Advanced Usage

### Using the Shell Wrapper

The `youtube-data` script automatically handles virtual environment activation:

```bash
# Make it globally accessible (optional)
sudo ln -s $(pwd)/youtube-data /usr/local/bin/youtube-data

# Then use from anywhere
youtube-data @channelname
```

### Python API Usage

You can also import and use the modules programmatically:

```python
from youtube_api import YouTubeAPI
from database import Database

api = YouTubeAPI("YOUR_API_KEY")
channel_id = "UCPix8N6PMRI4KzgyjuZeF0g"
playlist_id = api.get_uploads_playlist_id(channel_id)
video_ids = api.get_all_video_ids_from_playlist(playlist_id)
video_data = api.get_video_statistics(video_ids[:10])  # First 10 videos
```

### Configuration

To change the Google Sheets worksheet name, edit [config.py](config.py):

```python
WORKSHEET_NAME = "YourSheetName"
```

## Deactivating Virtual Environment

When done, deactivate the virtual environment:

```bash
deactivate
```

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


## Dependencies

- `google-api-python-client` - YouTube Data API
- `gspread` - Google Sheets API
- `google-auth` - Google authentication
- `oauth2client` - OAuth 2.0 client library
