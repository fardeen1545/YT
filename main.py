import streamlit as st
import requests
from datetime import datetime, timedelta
pip install isodate
import isodate

# YouTube API Key
API_KEY = "AIzaSyBuj2jKnx1ypRG61P56ouiw1M5SzH0JBaM"
YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
YOUTUBE_VIDEO_URL = "https://www.googleapis.com/youtube/v3/videos"
YOUTUBE_CHANNEL_URL = "https://www.googleapis.com/youtube/v3/channels"

# Streamlit App Title
st.title("YouTube Viral Topics Tool")

# Input Fields
days = st.number_input("Enter Days to Search (1-30):", min_value=1, max_value=30, value=5)

# User Input for Keyword, Views, Subs, and Video Length
st.sidebar.header("Filter Settings")
keyword_input = st.sidebar.text_input("Enter Keyword:", "Affair Relationship Stories")
min_views = st.sidebar.number_input("Minimum Views:", min_value=0, value=1000)
min_subs = st.sidebar.number_input("Minimum Subscribers:", min_value=0, value=3000)
min_duration = st.sidebar.number_input("Minimum Video Duration (in minutes):", min_value=0, value=1)
max_duration = st.sidebar.number_input("Maximum Video Duration (in minutes):", min_value=1, value=10)

# Fetch Data Button
if st.button("Fetch Data"):
    try:
        # Calculate date range
        start_date = (datetime.utcnow() - timedelta(days=int(days))).isoformat("T") + "Z"
        all_results = []

        # Define search parameters for the input keyword
        search_params = {
            "part": "snippet",
            "q": keyword_input,
            "type": "video",
            "order": "viewCount",
            "publishedAfter": start_date,
            "maxResults": 5,
            "key": API_KEY,
        }

        # Fetch video data
        response = requests.get(YOUTUBE_SEARCH_URL, params=search_params)
        data = response.json()

        # Check if "items" key exists
        if "items" not in data or not data["items"]:
            st.warning(f"No videos found for keyword: {keyword_input}")
        else:
            videos = data["items"]
            video_ids = [video["id"]["videoId"] for video in videos if "id" in video and "videoId" in video["id"]]
            channel_ids = [video["snippet"]["channelId"] for video in videos if "snippet" in video and "channelId" in video["snippet"]]

            if not video_ids or not channel_ids:
                st.warning(f"Skipping keyword: {keyword_input} due to missing video/channel data.")
            else:
                # Fetch video statistics
                stats_params = {"part": "statistics", "id": ",".join(video_ids), "key": API_KEY}
                stats_response = requests.get(YOUTUBE_VIDEO_URL, params=stats_params)
                stats_data = stats_response.json()

                if "items" not in stats_data or not stats_data["items"]:
                    st.warning(f"Failed to fetch video statistics for keyword: {keyword_input}")
                else:
                    # Fetch channel statistics
                    channel_params = {"part": "statistics", "id": ",".join(channel_ids), "key": API_KEY}
                    channel_response = requests.get(YOUTUBE_CHANNEL_URL, params=channel_params)
                    channel_data = channel_response.json()

                    if "items" not in channel_data or not channel_data["items"]:
                        st.warning(f"Failed to fetch channel statistics for keyword: {keyword_input}")
                    else:
                        # Fetch video duration (this is where we parse the video length)
                        video_params = {"part": "contentDetails", "id": ",".join(video_ids), "key": API_KEY}
                        video_response = requests.get(YOUTUBE_VIDEO_URL, params=video_params)
                        video_data = video_response.json()

                        if "items" not in video_data or not video_data["items"]:
                            st.warning(f"Failed to fetch video duration for keyword: {keyword_input}")
                        else:
                            stats = stats_data["items"]
                            channels = channel_data["items"]
                            video_details = video_data["items"]

                            # Collect results with user-defined filters
                            for video, stat, channel, details in zip(videos, stats, channels, video_details):
                                title = video["snippet"].get("title", "N/A")
                                description = video["snippet"].get("description", "")[:200]
                                video_url = f"https://www.youtube.com/watch?v={video['id']['videoId']}"
                                views = int(stat["statistics"].get("viewCount", 0))
                                subs = int(channel["statistics"].get("subscriberCount", 0))
                                duration_str = details["contentDetails"].get("duration", "PT0S")
                                
                                # Convert duration from ISO 8601 format to minutes
                                duration = isodate.parse_duration(duration_str)
                                duration_minutes = duration.total_seconds() / 60

                                # Filter results based on user-defined views, subscribers, and duration
                                if views >= min_views and subs >= min_subs and min_duration <= duration_minutes <= max_duration:
                                    all_results.append({
                                        "Title": title,
                                        "Description": description,
                                        "URL": video_url,
                                        "Views": views,
                                        "Subscribers": subs,
                                        "Duration (minutes)": duration_minutes,
                                        "Keyword": keyword_input
                                    })

        # Display results
        if all_results:
            st.success(f"Found {len(all_results)} results matching your filters!")
            for result in all_results:
                st.markdown(
                    f"**Title:** {result['Title']}  \n"
                    f"**Description:** {result['Description']}  \n"
                    f"**URL:** [Watch Video]({result['URL']})  \n"
                    f"**Views:** {result['Views']}  \n"
                    f"**Subscribers:** {result['Subscribers']}  \n"
                    f"**Duration (minutes):** {result['Duration (minutes)']}  \n"
                    f"**Keyword:** {result['Keyword']}"
                )
                st.write("---")
        else:
            st.warning("No results found matching your filters.")

    except Exception as e:
        st.error(f"An error occurred: {e}")
