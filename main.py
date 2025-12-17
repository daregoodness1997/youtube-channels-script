"""Main script for fetching YouTube channel data and storing it in a database and Google Sheets."""

import argparse
import re
import sys
from config import (
    API_KEY,
    YOUTUBE_API_SERVICE_NAME,
    YOUTUBE_API_VERSION,
    DATABASE_NAME,
    SPREADSHEET_ID,
    WORKSHEET_NAME,
)
from database import Database
from youtube_api import YouTubeAPI
from google_sheets import GoogleSheetsManager


def extract_video_id(input_string):
    """
    Extract video ID from various YouTube video URL formats.

    Supports:
    - https://www.youtube.com/watch?v=VIDEO_ID
    - https://youtu.be/VIDEO_ID
    - https://www.youtube.com/embed/VIDEO_ID
    - https://www.youtube.com/v/VIDEO_ID
    - VIDEO_ID (11 characters)

    Args:
        input_string: YouTube video URL or video ID

    Returns:
        Video ID string or None if not a video URL
    """
    # If it's already a video ID (11 chars, alphanumeric with - and _)
    if re.match(r"^[\w-]{11}$", input_string):
        return input_string

    # Extract from various video URL formats
    video_patterns = [
        r"(?:youtube\.com/watch\?v=|youtu\.be/)([\w-]{11})",
        r"youtube\.com/embed/([\w-]{11})",
        r"youtube\.com/v/([\w-]{11})",
    ]

    for pattern in video_patterns:
        match = re.search(pattern, input_string)
        if match:
            return match.group(1)

    return None


def extract_channel_id(input_string):
    """
    Extract channel ID from various YouTube URL formats or return the ID if already provided.

    Supports:
    - Channel ID: UCPix8N6PMRI4KzgyjuZeF0g
    - Channel URL: https://www.youtube.com/channel/UCPix8N6PMRI4KzgyjuZeF0g
    - Custom URL: https://www.youtube.com/@channelname
    - Old format: https://www.youtube.com/user/username
    - Short format: https://youtube.com/c/channelname

    Args:
        input_string: YouTube channel URL or channel ID

    Returns:
        Channel ID string or None if invalid
    """
    # If it's already a channel ID (starts with UC and ~24 chars)
    if re.match(r"^UC[\w-]{22}$", input_string):
        return input_string

    # Extract from various URL formats
    patterns = [
        r"youtube\.com/channel/([\w-]+)",
        r"youtube\.com/@([\w-]+)",
        r"youtube\.com/c/([\w-]+)",
        r"youtube\.com/user/([\w-]+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, input_string)
        if match:
            identifier = match.group(1)
            # If it starts with UC, it's already a channel ID
            if identifier.startswith("UC"):
                return identifier
            # Otherwise it's a handle/username, return it for lookup
            return identifier

    # If no pattern matched but it looks like a handle or username
    return input_string


def get_channel_id_from_handle(youtube_api, handle):
    """
    Get channel ID from a handle or username.

    Args:
        youtube_api: YouTubeAPI instance
        handle: YouTube handle (e.g., @channelname) or username

    Returns:
        Channel ID or None
    """
    try:
        # Remove @ if present
        handle = handle.lstrip("@")

        # Try searching for the channel
        response = (
            youtube_api.youtube.search()
            .list(part="snippet", q=handle, type="channel", maxResults=1)
            .execute()
        )

        if response.get("items"):
            return response["items"][0]["snippet"]["channelId"]
    except Exception as e:
        print(f"[ERROR] Could not find channel for handle '{handle}': {e}")

    return None


def process_single_video(
    youtube_api,
    video_id,
    database,
    sheets_manager=None,
    skip_transcripts=False,
    verbose=False,
):
    """
    Process a single video and store its data.

    Args:
        youtube_api: YouTubeAPI instance
        video_id: Single video ID
        database: Database instance
        sheets_manager: GoogleSheetsManager instance (optional)
        skip_transcripts: If True, skip fetching transcripts
        verbose: If True, print detailed debug information
    """
    print(f"\n[INFO] Fetching data for video: {video_id}")
    video_data_list = youtube_api.get_video_statistics(
        [video_id], skip_transcripts=skip_transcripts, verbose=verbose
    )

    if not video_data_list:
        print("[ERROR] Could not fetch video data. Video may be private or deleted.")
        return

    video_data = video_data_list[0]

    print("\n" + "=" * 60)
    print(f"Title: {video_data['title']}")
    print(f"URL: {video_data['video_url']}")
    print(f"Published: {video_data['published_at']}")
    print(
        f"Views: {video_data['view_count']:,} | "
        f"Likes: {video_data['like_count']:,} | "
        f"Comments: {video_data['comment_count']:,}"
    )
    if video_data["transcript"]:
        transcript_preview = (
            video_data["transcript"][:200] + "..."
            if len(video_data["transcript"]) > 200
            else video_data["transcript"]
        )
        print(f"\nTranscript Preview:\n{transcript_preview}")
    else:
        print(f"\nTranscript: Not Available")
    print("=" * 60 + "\n")

    # Save to database
    database.insert_video(
        video_data["id"],
        video_data["title"],
        video_data["video_url"],
        video_data["thumbnail_url"],
        video_data["published_at"],
        video_data["view_count"],
        video_data["like_count"],
        video_data["comment_count"],
        video_data["transcript"],
    )
    database.commit()

    # Save to Google Sheets if available
    if sheets_manager:
        sheets_manager.batch_insert_videos(video_data_list)
        print("[INFO] Data saved to Google Sheets")

    print(f"[SUCCESS] Video data saved to database")


def fetch_and_store_video_data(
    youtube_api,
    video_ids,
    database,
    sheets_manager=None,
    skip_transcripts=False,
    verbose=False,
):
    """
    Fetches statistics for each video and inserts them into the database and Google Sheets.

    Args:
        youtube_api: YouTubeAPI instance
        video_ids: List of video IDs to fetch
        database: Database instance
        sheets_manager: GoogleSheetsManager instance (optional)
        skip_transcripts: If True, skip fetching transcripts (faster)
        verbose: If True, print detailed debug information
    """
    for i in range(0, len(video_ids), 50):  # API supports up to 50 videos per call
        batch_ids = video_ids[i : i + 50]
        video_data_list = youtube_api.get_video_statistics(
            batch_ids, skip_transcripts=skip_transcripts, verbose=verbose
        )

        for video_data in video_data_list:
            print(f"Title: {video_data['title']}")
            print(f"URL: {video_data['video_url']}")
            print(f"Published: {video_data['published_at']}")
            print(
                f"Views: {video_data['view_count']}, "
                f"Likes: {video_data['like_count']}, "
                f"Comments: {video_data['comment_count']}"
            )
            if video_data["transcript"]:
                transcript_preview = (
                    video_data["transcript"][:100] + "..."
                    if len(video_data["transcript"]) > 100
                    else video_data["transcript"]
                )
                print(f"Transcript: {transcript_preview}")
            else:
                print(f"Transcript: Not Available")
            print("-" * 40)

            # Save to database
            database.insert_video(
                video_data["id"],
                video_data["title"],
                video_data["video_url"],
                video_data["thumbnail_url"],
                video_data["published_at"],
                video_data["view_count"],
                video_data["like_count"],
                video_data["comment_count"],
                video_data["transcript"],
            )

        database.commit()

        # Save batch to Google Sheets if available
        if sheets_manager:
            sheets_manager.batch_insert_videos(video_data_list)


def main(channel_input=None, skip_transcripts=False, verbose=False):
    """Main execution function.

    Args:
        channel_input: YouTube channel/video URL, handle, or ID (optional, will prompt if not provided)
        skip_transcripts: If True, skip fetching transcripts (faster processing)
        verbose: If True, print detailed debug information
    """
    # Get input from argument or prompt user
    if not channel_input:
        print("\n" + "=" * 60)
        print("YouTube Data API - Video/Channel Statistics Extractor")
        print("=" * 60)
        print("\nEnter a YouTube channel OR video in any of these formats:")
        print("\nChannel formats:")
        print("  - Channel ID: UCPix8N6PMRI4KzgyjuZeF0g")
        print("  - Channel URL: https://www.youtube.com/channel/UC...")
        print("  - Handle: @channelname or https://www.youtube.com/@channelname")
        print("  - Username: username or https://www.youtube.com/user/username")
        print("\nVideo formats:")
        print("  - Video URL: https://www.youtube.com/watch?v=VIDEO_ID")
        print("  - Short URL: https://youtu.be/VIDEO_ID")
        print("  - Video ID: dQw4w9WgXcQ")
        channel_input = input("\nChannel or Video: ").strip()

        if not channel_input:
            print("[ERROR] No input provided. Exiting.")
            sys.exit(1)

    # Check if input is a video URL/ID first
    print(f"\n[INFO] Processing input: {channel_input}")
    video_id = extract_video_id(channel_input)

    if video_id:
        # Process single video
        print(f"[INFO] Detected video ID: {video_id}")

        # Initialize YouTube API
        youtube_api = YouTubeAPI(API_KEY, YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION)

        # Initialize Google Sheets (optional)
        sheets_manager = GoogleSheetsManager(SPREADSHEET_ID, WORKSHEET_NAME)
        sheets_enabled = sheets_manager.authenticate()

        if sheets_enabled:
            print("[INFO] Google Sheets connected successfully")
            sheets_manager.setup_headers()
        else:
            print(
                "[WARNING] Google Sheets not available. Data will only be saved to database."
            )
            sheets_manager = None

        # Setup database and process video
        with Database(DATABASE_NAME) as db:
            print("[INFO] Setting up database...")
            db.setup_table()

            if skip_transcripts:
                print("[INFO] Skipping transcripts for faster processing")

            process_single_video(
                youtube_api, video_id, db, sheets_manager, skip_transcripts, verbose
            )

        return

    # Otherwise, process as channel
    channel_id = extract_channel_id(channel_input)

    # Initialize YouTube API
    youtube_api = YouTubeAPI(API_KEY, YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION)

    # If we got a handle/username instead of ID, look it up
    if not channel_id.startswith("UC"):
        print(f"[INFO] Looking up channel ID for: {channel_id}")
        channel_id = get_channel_id_from_handle(youtube_api, channel_id)
        if not channel_id:
            print(
                "[ERROR] Could not find channel. Please check the input and try again."
            )
            sys.exit(1)

    print(f"[INFO] Using channel ID: {channel_id}")

    # Initialize Google Sheets (optional)
    sheets_manager = GoogleSheetsManager(SPREADSHEET_ID, WORKSHEET_NAME)
    sheets_enabled = sheets_manager.authenticate()

    if sheets_enabled:
        print("[INFO] Google Sheets connected successfully")
        sheets_manager.setup_headers()
    else:
        print(
            "[WARNING] Google Sheets not available. Data will only be saved to database."
        )
        sheets_manager = None

    # Setup database using context manager
    with Database(DATABASE_NAME) as db:
        print("[INFO] Setting up database...")
        db.setup_table()

        print("[INFO] Fetching uploads playlist ID...")
        uploads_playlist_id = youtube_api.get_uploads_playlist_id(channel_id)

        print("[INFO] Fetching all video IDs from playlist...")
        video_ids = youtube_api.get_all_video_ids_from_playlist(uploads_playlist_id)
        print(f"[INFO] Total videos found: {len(video_ids)}")

        print("[INFO] Fetching video statistics and saving to database...")
        if skip_transcripts:
            print("[INFO] Skipping transcripts for faster processing")
        fetch_and_store_video_data(
            youtube_api,
            video_ids,
            db,
            sheets_manager,
            skip_transcripts=skip_transcripts,
        )

    success_message = f"[SUCCESS] YouTube video statistics saved to '{DATABASE_NAME}'"
    if sheets_enabled:
        success_message += " and Google Sheets"
    print(success_message + ".")


# === Run Script ===
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Fetch YouTube channel or video statistics and save to database and Google Sheets",
        epilog="Examples:\n"
        "  # Channel examples\n"
        "  python main.py UCPix8N6PMRI4KzgyjuZeF0g\n"
        "  python main.py https://www.youtube.com/@channelname\n"
        "  python main.py https://www.youtube.com/channel/UC...\n\n"
        "  # Video examples\n"
        "  python main.py https://www.youtube.com/watch?v=dQw4w9WgXcQ\n"
        "  python main.py https://youtu.be/dQw4w9WgXcQ\n"
        "  python main.py dQw4w9WgXcQ\n\n"
        "  # Interactive mode\n"
        "  python main.py",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "channel",
        nargs="?",
        help="YouTube channel URL, handle, channel ID, video URL, or video ID",
    )
    parser.add_argument(
        "--no-sheets",
        action="store_true",
        help="Skip Google Sheets export (database only)",
    )
    parser.add_argument(
        "--no-transcripts",
        action="store_true",
        help="Skip fetching video transcripts (faster processing)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Print detailed debug information",
    )

    args = parser.parse_args()

    try:
        main(args.channel, skip_transcripts=args.no_transcripts, verbose=args.verbose)
    except KeyboardInterrupt:
        print("\n\n[INFO] Process interrupted by user. Exiting...")
        sys.exit(0)
    except Exception as e:
        print(f"\n[ERROR] An unexpected error occurred: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
