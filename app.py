"""Streamlit Web UI for YouTube Data Extractor."""

import streamlit as st
import pandas as pd
import re
from io import StringIO
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
from main import (
    extract_video_id,
    extract_channel_id,
    get_channel_id_from_handle,
)


def extract_spreadsheet_id(sheet_url):
    """
    Extract spreadsheet ID from Google Sheets URL.

    Args:
        sheet_url: Google Sheets URL or spreadsheet ID

    Returns:
        Spreadsheet ID or None if invalid
    """
    # If it's already an ID (alphanumeric string)
    if re.match(r"^[a-zA-Z0-9_-]{30,}$", sheet_url.strip()):
        return sheet_url.strip()

    # Extract from URL
    pattern = r"/spreadsheets/d/([a-zA-Z0-9_-]+)"
    match = re.search(pattern, sheet_url)
    if match:
        return match.group(1)

    return None


# Page configuration
st.set_page_config(
    page_title="YouTube Data Extractor",
    page_icon="🎥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown(
    """
    <style>
    .main-header {
        font-size: 3rem;
        color: #FF0000;
        text-align: center;
        margin-bottom: 2rem;
    }
    .stProgress > div > div > div > div {
        background-color: #FF0000;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# Header
st.markdown(
    '<h1 class="main-header">🎥 YouTube Data Extractor</h1>', unsafe_allow_html=True
)
st.markdown("---")

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")

    skip_transcripts = st.checkbox(
        "Skip Transcripts",
        value=False,
        help="Skip fetching video transcripts for faster processing",
    )

    st.markdown("---")
    st.subheader("📊 Google Sheets Export")

    skip_sheets = st.checkbox(
        "Skip Google Sheets",
        value=False,
        help="Only save to local database, skip Google Sheets export",
    )

    use_custom_sheet = st.checkbox(
        "Use Custom Google Sheet",
        value=False,
        disabled=skip_sheets,
        help="Provide your own Google Sheet URL",
    )

    custom_sheet_url = None
    custom_worksheet_name = "Sheet1"

    if use_custom_sheet and not skip_sheets:
        custom_sheet_url = st.text_input(
            "Google Sheet URL",
            placeholder="https://docs.google.com/spreadsheets/d/...",
            help="Paste your Google Sheets URL here",
        )
        custom_worksheet_name = st.text_input(
            "Worksheet Name",
            value="Sheet1",
            help="Name of the worksheet tab (default: Sheet1)",
        )
        st.caption(
            "⚠️ **Share the sheet with:** `youtube-data-api@useeducator.iam.gserviceaccount.com`"
        )

    verbose = st.checkbox("Verbose Mode", help="Show detailed debug information")

    st.markdown("---")
    st.header("📊 Data Storage")
    st.info(f"**Database:** {DATABASE_NAME}")
    if not skip_sheets:
        if use_custom_sheet and custom_sheet_url:
            sheet_id = extract_spreadsheet_id(custom_sheet_url)
            if sheet_id:
                st.info(f"**Custom Sheet:** {sheet_id[:20]}...")
            else:
                st.warning("⚠️ Invalid Sheet URL")
        else:
            st.info(f"**Default Sheet:** {SPREADSHEET_ID[:20]}...")

    st.markdown("---")
    st.header("ℹ️ About")
    st.markdown(
        """
    This tool extracts data from YouTube channels and videos including:
    - Title, URL, Thumbnail
    - Views, Likes, Comments
    - Published Date
    - Transcripts (optional)
    
    **To use a custom Google Sheet:**
    1. Create a new Google Sheet or use existing
    2. Share it with: `youtube-data-api@useeducator.iam.gserviceaccount.com` (Editor access)
    3. Enable "Use Custom Google Sheet" above
    4. Paste the sheet URL
    """
    )

# Navigation tabs
tab1, tab2 = st.tabs(["📥 Extract Data", "📊 View Data"])

# Tab 1: Extract Data
with tab1:
    col1, col2 = st.columns([2, 1])

    with col1:
        st.header("🔗 Input")
        input_type = st.radio(
            "What do you want to extract?",
            ["📺 Channel (all videos)", "🎬 Single Video"],
            horizontal=True,
        )

        if input_type == "📺 Channel (all videos)":
            channel_input = st.text_input(
                "Channel URL, Handle, or ID",
                placeholder="https://www.youtube.com/@channelname or UCxxx...",
                help="Enter any YouTube channel format",
            )
            st.caption("**Supported formats:** @channelname, channel URL, channel ID")
        else:
            video_input = st.text_input(
                "Video URL or ID",
                placeholder="https://www.youtube.com/watch?v=xxx or video_id",
                help="Enter any YouTube video format",
            )
            st.caption(
                "**Supported formats:** Video URL, short URL (youtu.be), video ID"
            )

    with col2:
        st.header("📝 Examples")
        st.code("@MrBeast", language="text")
        st.code("https://youtu.be/dQw4w9WgXcQ", language="text")
        st.code("UCX6OQ3DkcsbYNE6H8uQQuVA", language="text")

    # Process button
    st.markdown("---")
    if st.button("🚀 Extract Data", type="primary", use_container_width=True):

        # Validate input
        if input_type == "📺 Channel (all videos)":
            if not channel_input:
                st.error("❌ Please enter a channel URL, handle, or ID")
                st.stop()
            user_input = channel_input
            is_video = False
        else:
            if not video_input:
                st.error("❌ Please enter a video URL or ID")
                st.stop()
            user_input = video_input
            is_video = True

        # Progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()

        try:
            # Initialize API
            status_text.text("🔧 Initializing YouTube API...")
            progress_bar.progress(10)
            youtube_api = YouTubeAPI(
                API_KEY, YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION
            )

            # Initialize Google Sheets if needed
            sheets_manager = None
            if not skip_sheets:
                status_text.text("📊 Connecting to Google Sheets...")
                progress_bar.progress(20)

                # Determine which spreadsheet to use
                target_spreadsheet_id = SPREADSHEET_ID
                target_worksheet_name = WORKSHEET_NAME

                if use_custom_sheet and custom_sheet_url:
                    extracted_id = extract_spreadsheet_id(custom_sheet_url)
                    if extracted_id:
                        target_spreadsheet_id = extracted_id
                        target_worksheet_name = custom_worksheet_name
                        st.info(
                            f"📊 Using custom spreadsheet: {target_spreadsheet_id[:20]}..."
                        )
                    else:
                        st.warning("⚠️ Invalid custom sheet URL, using default sheet")

                sheets_manager = GoogleSheetsManager(
                    target_spreadsheet_id, target_worksheet_name
                )
                if sheets_manager.authenticate():
                    sheets_manager.setup_headers()
                    st.sidebar.success("✅ Google Sheets connected")
                else:
                    st.sidebar.warning("⚠️ Google Sheets unavailable")
                    sheets_manager = None

            # Process input
            status_text.text("🔍 Processing input...")
            progress_bar.progress(30)

            video_data_list = []

            if is_video:
                # Single video
                video_id = extract_video_id(user_input)
                if not video_id:
                    st.error("❌ Invalid video URL or ID")
                    st.stop()

                status_text.text(f"📥 Fetching video data: {video_id}")
                progress_bar.progress(50)

                if verbose:
                    st.info(f"Debug: skip_transcripts = {skip_transcripts}")

                video_data_list = youtube_api.get_video_statistics(
                    [video_id], skip_transcripts=skip_transcripts, verbose=verbose
                )

            else:
                # Channel
                channel_id = extract_channel_id(user_input)

                if not channel_id.startswith("UC"):
                    status_text.text(f"🔍 Looking up channel: {channel_id}")
                    channel_id = get_channel_id_from_handle(youtube_api, channel_id)
                    if not channel_id:
                        st.error("❌ Could not find channel")
                        st.stop()

                status_text.text("📋 Fetching video list...")
                progress_bar.progress(40)

                uploads_playlist_id = youtube_api.get_uploads_playlist_id(channel_id)
                video_ids = youtube_api.get_all_video_ids_from_playlist(
                    uploads_playlist_id
                )

                st.info(f"📊 Found {len(video_ids)} videos")

                # Fetch video data in batches
                for i in range(0, len(video_ids), 50):
                    batch_ids = video_ids[i : i + 50]
                    progress = 50 + (i / len(video_ids) * 40)
                    progress_bar.progress(int(progress))
                    status_text.text(
                        f"📥 Fetching videos {i+1}-{min(i+50, len(video_ids))} of {len(video_ids)}..."
                    )

                    batch_data = youtube_api.get_video_statistics(
                        batch_ids, skip_transcripts=skip_transcripts, verbose=verbose
                    )
                    video_data_list.extend(batch_data)

            # Save to database
            status_text.text("💾 Saving to database...")
            progress_bar.progress(90)

            with Database(DATABASE_NAME) as db:
                db.setup_table()
                for video_data in video_data_list:
                    db.insert_video(
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
                db.commit()

            # Save to Google Sheets
            if sheets_manager:
                status_text.text("📤 Exporting to Google Sheets...")
                sheets_manager.batch_insert_videos(video_data_list)

            progress_bar.progress(100)
            status_text.text("✅ Complete!")

            # Display results
            st.success(
                f"✅ Successfully extracted data from {len(video_data_list)} video(s)!"
            )

            # Create DataFrame
            df = pd.DataFrame(video_data_list)

            # Reorder and format columns
            columns_order = [
                "title",
                "video_url",
                "published_at",
                "view_count",
                "like_count",
                "comment_count",
            ]
            if not skip_transcripts:
                columns_order.append("transcript")

            df_display = df[columns_order].copy()
            df_display.columns = [
                "Title",
                "URL",
                "Published",
                "Views",
                "Likes",
                "Comments",
            ] + (["Transcript"] if not skip_transcripts else [])

            # Display summary stats
            st.markdown("---")
            st.header("📈 Summary Statistics")

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Videos", len(video_data_list))
            with col2:
                st.metric("Total Views", f"{df['view_count'].sum():,}")
            with col3:
                st.metric("Total Likes", f"{df['like_count'].sum():,}")
            with col4:
                st.metric("Total Comments", f"{df['comment_count'].sum():,}")

            # Display data table
            st.markdown("---")
            st.header("📋 Video Data")

            # Truncate transcript for display
            if not skip_transcripts and "Transcript" in df_display.columns:
                df_display["Transcript"] = df_display["Transcript"].apply(
                    lambda x: (
                        (str(x)[:100] + "...")
                        if pd.notna(x) and len(str(x)) > 100
                        else x
                    )
                )

            st.dataframe(
                df_display,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "URL": st.column_config.LinkColumn("URL"),
                    "Views": st.column_config.NumberColumn("Views", format="%d"),
                    "Likes": st.column_config.NumberColumn("Likes", format="%d"),
                    "Comments": st.column_config.NumberColumn("Comments", format="%d"),
                },
            )

            # Download button
            csv = df_display.to_csv(index=False)
            st.download_button(
                label="📥 Download as CSV",
                data=csv,
                file_name=f"youtube_data_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True,
            )

        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
            if verbose:
                st.exception(e)

# Tab 2: View Data
with tab2:
    st.header("📊 Database Viewer")
    st.markdown("View all previously extracted YouTube video data from the database.")

    # Refresh button and filters
    col1, col2 = st.columns([1, 3])
    with col1:
        refresh = st.button("🔄 Refresh Data", use_container_width=True)

    try:
        # Load data from database
        with Database(DATABASE_NAME) as db:
            db.setup_table()
            db.cursor.execute(
                """
                SELECT id, title, video_url, thumbnail_url, published_at, 
                       view_count, like_count, comment_count, transcript
                FROM videos
                ORDER BY published_at DESC
            """
            )
            rows = db.cursor.fetchall()

        if not rows:
            st.info("📭 No data found in database. Extract some videos first!")
        else:
            # Convert to DataFrame
            df = pd.DataFrame(
                rows,
                columns=[
                    "ID",
                    "Title",
                    "URL",
                    "Thumbnail",
                    "Published",
                    "Views",
                    "Likes",
                    "Comments",
                    "Transcript",
                ],
            )

            # Filters
            st.markdown("---")
            st.subheader("🔍 Filters")

            col1, col2, col3 = st.columns(3)
            with col1:
                search_term = st.text_input(
                    "🔎 Search titles", placeholder="Enter keywords..."
                )
            with col2:
                min_views = st.number_input(
                    "Min Views", min_value=0, value=0, step=1000
                )
            with col3:
                sort_by = st.selectbox(
                    "Sort by",
                    [
                        "Published Date (newest)",
                        "Published Date (oldest)",
                        "Views (high-low)",
                        "Views (low-high)",
                        "Likes (high-low)",
                        "Comments (high-low)",
                    ],
                )

            # Apply filters
            filtered_df = df.copy()

            if search_term:
                filtered_df = filtered_df[
                    filtered_df["Title"].str.contains(search_term, case=False, na=False)
                ]

            if min_views > 0:
                filtered_df = filtered_df[filtered_df["Views"] >= min_views]

            # Apply sorting
            if sort_by == "Published Date (newest)":
                filtered_df = filtered_df.sort_values("Published", ascending=False)
            elif sort_by == "Published Date (oldest)":
                filtered_df = filtered_df.sort_values("Published", ascending=True)
            elif sort_by == "Views (high-low)":
                filtered_df = filtered_df.sort_values("Views", ascending=False)
            elif sort_by == "Views (low-high)":
                filtered_df = filtered_df.sort_values("Views", ascending=True)
            elif sort_by == "Likes (high-low)":
                filtered_df = filtered_df.sort_values("Likes", ascending=False)
            elif sort_by == "Comments (high-low)":
                filtered_df = filtered_df.sort_values("Comments", ascending=False)

            # Summary statistics
            st.markdown("---")
            st.subheader("📈 Statistics")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Videos", len(filtered_df))
            with col2:
                st.metric("Total Views", f"{filtered_df['Views'].sum():,}")
            with col3:
                st.metric("Total Likes", f"{filtered_df['Likes'].sum():,}")
            with col4:
                st.metric("Total Comments", f"{filtered_df['Comments'].sum():,}")

            # Display data
            st.markdown("---")
            st.subheader("📋 Video Records")

            # Prepare display DataFrame
            display_df = filtered_df[
                ["Title", "URL", "Published", "Views", "Likes", "Comments"]
            ].copy()

            # Truncate titles if too long
            display_df["Title"] = display_df["Title"].apply(
                lambda x: (x[:80] + "...") if len(str(x)) > 80 else x
            )

            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "URL": st.column_config.LinkColumn("URL"),
                    "Views": st.column_config.NumberColumn("Views", format="%d"),
                    "Likes": st.column_config.NumberColumn("Likes", format="%d"),
                    "Comments": st.column_config.NumberColumn("Comments", format="%d"),
                },
            )

            # Export options
            st.markdown("---")
            col1, col2 = st.columns(2)

            with col1:
                # Download CSV
                csv = filtered_df.to_csv(index=False)
                st.download_button(
                    label="📥 Download Filtered Data as CSV",
                    data=csv,
                    file_name=f"youtube_data_export_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    use_container_width=True,
                )

            with col2:
                # Delete all data
                if st.button(
                    "🗑️ Clear All Database Data",
                    type="secondary",
                    use_container_width=True,
                ):
                    if st.session_state.get("confirm_delete", False):
                        with Database(DATABASE_NAME) as db:
                            db.cursor.execute("DELETE FROM videos")
                            db.commit()
                        st.success("✅ Database cleared!")
                        st.rerun()
                    else:
                        st.session_state["confirm_delete"] = True
                        st.warning("⚠️ Click again to confirm deletion")

    except Exception as e:
        st.error(f"❌ Error loading data: {str(e)}")
        st.exception(e)

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray;'>Made with ❤️ using Streamlit | YouTube Data API v3</div>",
    unsafe_allow_html=True,
)
