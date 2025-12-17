"""Google Sheets operations for storing YouTube video data."""

import gspread
from google.oauth2.service_account import Credentials
import os
import json


class GoogleSheetsManager:
    """Handles Google Sheets operations for storing video data."""

    def __init__(
        self,
        spreadsheet_id,
        worksheet_name="Sheet1",
        credentials_file="credentials.json",
    ):
        """
        Initialize Google Sheets manager.

        Args:
            spreadsheet_id: The ID of the Google Spreadsheet
            worksheet_name: The name of the worksheet to use
            credentials_file: Path to the service account credentials JSON file
        """
        self.spreadsheet_id = spreadsheet_id
        self.worksheet_name = worksheet_name
        self.credentials_file = credentials_file
        self.client = None
        self.sheet = None

    def authenticate(self):
        """Authenticate with Google Sheets API using service account credentials."""
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]

        try:
            # Try to get credentials from Streamlit secrets first (for deployment)
            try:
                import streamlit as st

                if hasattr(st, "secrets") and "gcp_service_account" in st.secrets:
                    # Use Streamlit secrets
                    creds_dict = dict(st.secrets["gcp_service_account"])
                    creds = Credentials.from_service_account_info(
                        creds_dict, scopes=scopes
                    )
                else:
                    # Fall back to credentials file
                    creds = Credentials.from_service_account_file(
                        self.credentials_file, scopes=scopes
                    )
            except (ImportError, FileNotFoundError):
                # Streamlit not available or no secrets, use credentials file
                creds = Credentials.from_service_account_file(
                    self.credentials_file, scopes=scopes
                )

            self.client = gspread.authorize(creds)
            spreadsheet = self.client.open_by_key(self.spreadsheet_id)

            # Try to access worksheet with exact name, then try with stripped whitespace
            try:
                self.sheet = spreadsheet.worksheet(self.worksheet_name)
            except Exception:
                # Try finding worksheet with matching stripped name
                for ws in spreadsheet.worksheets():
                    if ws.title.strip() == self.worksheet_name.strip():
                        self.sheet = ws
                        break
                else:
                    raise

            return True
        except Exception as e:
            print(f"[ERROR] Failed to authenticate with Google Sheets: {e}")
            return False

    def setup_headers(self):
        """Set up the header row if it doesn't exist."""
        try:
            # Check if headers already exist
            existing_headers = self.sheet.row_values(1)
            if not existing_headers or existing_headers[0] != "Video ID":
                headers = [
                    "Video ID",
                    "Title",
                    "Video URL",
                    "Thumbnail URL",
                    "Published Date",
                    "View Count",
                    "Like Count",
                    "Comment Count",
                    "Transcript",
                ]
                self.sheet.update("A1:I1", [headers])
                print("[INFO] Headers set up in Google Sheets")
        except Exception as e:
            print(f"[ERROR] Failed to set up headers: {e}")

    def insert_video(self, video_id, title, view_count, like_count, comment_count):
        """
        Insert or update a video record in Google Sheets.

        Args:
            video_id: The video ID
            title: The video title
            view_count: Number of views
            like_count: Number of likes
            comment_count: Number of comments
        """
        try:
            # Check if video already exists
            cell = self.sheet.find(video_id, in_column=1)

            row_data = [video_id, title, view_count, like_count, comment_count]

            if cell:
                # Update existing row
                row_number = cell.row
                self.sheet.update(f"A{row_number}:E{row_number}", [row_data])
            else:
                # Append new row
                self.sheet.append_row(row_data)
        except Exception as e:
            print(f"[WARNING] Failed to insert video {video_id} to Google Sheets: {e}")

    def batch_insert_videos(self, video_data_list):
        """
        Insert multiple video records at once for better performance.

        Args:
            video_data_list: List of video data dictionaries
        """
        try:
            # Get all existing video IDs
            existing_ids = self.sheet.col_values(1)[1:]  # Skip header

            rows_to_append = []
            rows_to_update = []

            for video_data in video_data_list:
                row_data = [
                    video_data["id"],
                    video_data["title"],
                    video_data["video_url"],
                    video_data["thumbnail_url"],
                    video_data["published_at"],
                    video_data["view_count"],
                    video_data["like_count"],
                    video_data["comment_count"],
                    video_data["transcript"],
                ]

                if video_data["id"] in existing_ids:
                    # Find row number and prepare update
                    row_num = (
                        existing_ids.index(video_data["id"]) + 2
                    )  # +2 for header and 0-index
                    rows_to_update.append((row_num, row_data))
                else:
                    rows_to_append.append(row_data)

            # Perform batch operations
            if rows_to_append:
                self.sheet.append_rows(rows_to_append)
                print(f"[INFO] Added {len(rows_to_append)} new videos to Google Sheets")

            if rows_to_update:
                for row_num, row_data in rows_to_update:
                    self.sheet.update(f"A{row_num}:I{row_num}", [row_data])
                print(
                    f"[INFO] Updated {len(rows_to_update)} existing videos in Google Sheets"
                )

        except Exception as e:
            print(f"[ERROR] Failed to batch insert videos: {e}")
