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

The easiest way to use the application:

```bash
./youtube-data https://www.youtube.com/@channelname
```

Or with just a channel ID:

```bash
./youtube-data UCPix8N6PMRI4KzgyjuZeF0g
```

### Command Line Options

```bash
# Using channel URL
python main.py https://www.youtube.com/@channelname

# Using channel ID
python main.py UCPix8N6PMRI4KzgyjuZeF0g

# Interactive mode (will prompt for input)
python main.py

# Skip Google Sheets export (database only)
python main.py UCPix8N6PMRI4KzgyjuZeF0g --no-sheets

# Skip transcripts for faster processing
python main.py UCPix8N6PMRI4KzgyjuZeF0g --no-transcripts
```

### Supported Channel Formats

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

## Dependencies

- `google-api-python-client` - YouTube Data API
- `gspread` - Google Sheets API
- `google-auth` - Google authentication
- `oauth2client` - OAuth 2.0 client library
