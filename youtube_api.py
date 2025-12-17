"""YouTube API operations for fetching channel and video data."""

from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi
from datetime import datetime


class YouTubeAPI:
    """Handles YouTube API interactions."""

    def __init__(self, api_key, service_name="youtube", version="v3"):
        """Initialize YouTube API client."""
        self.youtube = build(service_name, version, developerKey=api_key)

    def get_uploads_playlist_id(self, channel_id):
        """
        Returns the uploads playlist ID for a given YouTube channel ID.

        Args:
            channel_id: The YouTube channel ID

        Returns:
            The uploads playlist ID
        """
        response = (
            self.youtube.channels().list(part="contentDetails", id=channel_id).execute()
        )
        return response["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

    def get_all_video_ids_from_playlist(self, playlist_id):
        """
        Returns a list of all video IDs in a given uploads playlist.

        Args:
            playlist_id: The playlist ID to fetch videos from

        Returns:
            List of video IDs
        """
        video_ids = []
        next_page_token = None

        while True:
            response = (
                self.youtube.playlistItems()
                .list(
                    part="contentDetails",
                    playlistId=playlist_id,
                    maxResults=50,
                    pageToken=next_page_token,
                )
                .execute()
            )

            for item in response["items"]:
                video_ids.append(item["contentDetails"]["videoId"])

            next_page_token = response.get("nextPageToken")
            if not next_page_token:
                break

        return video_ids

    def get_video_statistics(self, video_ids):
        """
        Fetch comprehensive data for a list of video IDs.

        Args:
            video_ids: List of video IDs (max 50)

        Returns:
            List of video data dictionaries with all available information
        """
        response = (
            self.youtube.videos()
            .list(part="snippet,statistics,contentDetails", id=",".join(video_ids))
            .execute()
        )

        video_data = []
        for video in response["items"]:
            video_id = video["id"]
            snippet = video["snippet"]
            stats = video["statistics"]

            # Get thumbnail URL (prefer maxres, fall back to high, then default)
            thumbnails = snippet.get("thumbnails", {})
            thumbnail_url = (
                thumbnails.get("maxres", {}).get("url")
                or thumbnails.get("high", {}).get("url")
                or thumbnails.get("default", {}).get("url")
            )

            # Parse published date
            published_at = snippet.get("publishedAt", "")

            # Generate video URL
            video_url = f"https://www.youtube.com/watch?v={video_id}"

            # Fetch transcript
            transcript_text = self.get_video_transcript(video_id)

            video_info = {
                "id": video_id,
                "title": snippet.get("title", ""),
                "video_url": video_url,
                "thumbnail_url": thumbnail_url,
                "published_at": published_at,
                "view_count": int(stats["viewCount"]) if "viewCount" in stats else None,
                "like_count": int(stats["likeCount"]) if "likeCount" in stats else None,
                "comment_count": (
                    int(stats["commentCount"]) if "commentCount" in stats else None
                ),
                "transcript": transcript_text,
            }
            video_data.append(video_info)

        return video_data

    def get_video_transcript(self, video_id, verbose=False):
        """
        Fetch transcript for a video with multiple language fallbacks.

        Args:
            video_id: The YouTube video ID
            verbose: Print detailed error messages

        Returns:
            Transcript text as a string, or None if not available
        """
        try:
            # Try to get transcript in any available language
            # First, try to get a list of available transcripts
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

            # Try to find manually created transcripts first (usually better quality)
            try:
                # Try English first
                transcript = transcript_list.find_manually_created_transcript(["en"])
                transcript_data = transcript.fetch()
            except:
                # Try any manually created transcript
                try:
                    transcript = transcript_list.find_manually_created_transcript(
                        ["en", "es", "fr", "de", "pt", "ja", "ko", "zh", "ar"]
                    )
                    transcript_data = transcript.fetch()
                except:
                    # Fall back to generated transcripts
                    try:
                        transcript = transcript_list.find_generated_transcript(["en"])
                        transcript_data = transcript.fetch()
                    except:
                        # Try any available generated transcript
                        transcript = transcript_list.find_generated_transcript(
                            ["en", "es", "fr", "de", "pt", "ja", "ko", "zh", "ar"]
                        )
                        transcript_data = transcript.fetch()

            # Combine all transcript segments into one text
            transcript_text = " ".join([entry["text"] for entry in transcript_data])
            return transcript_text if transcript_text.strip() else None

        except Exception as e:
            # Transcript might not be available (disabled, private, etc.)
            if verbose:
                print(f"[DEBUG] No transcript for video {video_id}: {e}")
            return None
