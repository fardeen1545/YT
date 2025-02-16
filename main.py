import streamlit as st
import requests
from datetime import datetime, timedelta

# YouTube API Key
API_KEY = "AIzaSyBuj2jKnx1ypRG61P56ouiw1M5SzH0JBaM"
YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
YOUTUBE_VIDEO_URL = "https://www.googleapis.com/youtube/v3/videos"
YOUTUBE_CHANNEL_URL = "https://www.googleapis.com/youtube/v3/channels"

# Streamlit App Title
st.title("YouTube Viral Topics Tool")

# Input Fields
days = st.number_input("Enter Days to Search (1-30):", min_value=1, max_value=30, value=5)

# User Input for Keyword, Views, and Subs
st.sidebar.header("Filter Settings")
keyword_input = st.sidebar.text_input("Enter Keyword:", "Affair Relationship Stories")
min_views = st.sidebar.number_input("Minimum Views:", min_value=0, value=1000)
min_subs = st.sidebar.number_input("Minimum Subscribers:", min_value=0, value=3000)

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
                        stats = stats_data["items"]
                        channels = channel_data["items"]

                        # Collect results with user-defined filters
                        for video, stat, channel in zip(videos, stats, channels):
                            title = video["snippet"].get("title", "N/A")
                            description = video["snippet"].get("description", "")[:200]
                            video_url = f"https://www.youtube.com/watch?v={video['id']['videoId']}"
                            views = int(stat["statistics"].get("viewCount", 0))
                            subs = int(channel["statistics"].get("subscriberCount", 0))

                            # Filter results based on user-defined views and subscriber count
                            if views >= min_views and subs >= min_subs:
                                all_results.append({
                                    "Title": title,
                                    "Description": description,
                                    "URL": video_url,
                                    "Views": views,
                                    "Subscribers": subs,
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
                    f"**Keyword:** {result['Keyword']}"
                )
                st.write("---")
        else:
            st.warning("No results found matching your filters.")

    except Exception as e:
        st.error(f"An error occurred: {e}")
