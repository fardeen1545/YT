import streamlit as st
import requests
from datetime import datetime, timedelta
import isodate  # Required for parsing ISO 8601 durations

# ✅ Directly adding API Key (Replace with your actual key)
API_KEY = AIzaSyBuj2jKnx1ypRG61P56ouiw1M5SzH0JBaM

YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
YOUTUBE_VIDEO_URL = "https://www.googleapis.com/youtube/v3/videos"
YOUTUBE_CHANNEL_URL = "https://www.googleapis.com/youtube/v3/channels"

# Streamlit App Title
st.title("YouTube Viral Topics Tool")

# Input Fields
days = st.number_input("Enter Days to Search (1-30):", min_value=1, max_value=30, value=5)
min_views = st.number_input("Minimum Views:", min_value=1000, max_value=1000000, value=10000)

# List of broader keywords
keywords = [
    "Jon Snow", "Daenerys Targaryen", "Tyrion Lannister", "Arya Stark", 
    "Sansa Stark", "Bran Stark", "Cersei Lannister", "Jaime Lannister", 
    "Tywin Lannister", "Joffrey Baratheon", "Robb Stark", "Ned Stark", 
    "Stannis Baratheon", "Melisandre", "Davos Seaworth", "Theon Greyjoy", 
    "Yara Greyjoy", "Brienne of Tarth", "Samwell Tarly", "Jorah Mormont", 
    "Varys", "Petyr Baelish", "Sandor Clegane", "Gregor Clegane", 
    "Ramsay Bolton", "Roose Bolton", "Gendry", "Missandei", "Grey Worm", 
    "Euron Greyjoy", "Olenna Tyrell", "Margaery Tyrell", "Loras Tyrell", 
    "Barristan Selmy", "Tormund Giantsbane", "Beric Dondarrion", 
    "Benjen Stark", "Khal Drogo", "Shae", "Qyburn", "High Sparrow", "Night King"
]

# ✅ Ensure the API key is correctly set
if not API_KEY or API_KEY == "your_api_key_here":
    st.error("⚠️ API Key is missing! Please add a valid YouTube API Key in the script.")
    st.stop()

# Fetch Data Button
if st.button("Fetch Data"):
    try:
        # Calculate date range
        start_date = (datetime.utcnow() - timedelta(days=int(days))).isoformat("T") + "Z"
        all_results = []

        # Search for all keywords in a single batch
        keyword_query = "|".join(keywords)  # Use | to search for multiple terms
        st.write(f"Searching for keywords: {keyword_query}")

        # Define search parameters
        search_params = {
            "part": "snippet",
            "q": keyword_query,
            "type": "video",
            "order": "viewCount",
            "publishedAfter": start_date,
            "maxResults": 50,  # Increase to get better results
            "key": API_KEY,
        }

        # Fetch video data
        response = requests.get(YOUTUBE_SEARCH_URL, params=search_params)
        data = response.json()

        # Check if "items" key exists
        if "items" not in data or not data["items"]:
            st.warning("No videos found for the given keywords.")
        else:
            videos = data["items"]
            video_ids = [video["id"]["videoId"] for video in videos if "id" in video and "videoId" in video["id"]]
            channel_ids = [video["snippet"]["channelId"] for video in videos if "snippet" in video and "channelId" in video["snippet"]]

            # Fetch video statistics and content details (duration)
            stats_params = {
                "part": "statistics,contentDetails",
                "id": ",".join(video_ids),
                "key": API_KEY
            }
            stats_response = requests.get(YOUTUBE_VIDEO_URL, params=stats_params)
            stats_data = stats_response.json()

            # Fetch channel statistics in bulk
            channel_params = {"part": "statistics", "id": ",".join(channel_ids), "key": API_KEY}
            channel_response = requests.get(YOUTUBE_CHANNEL_URL, params=channel_params)
            channel_data = channel_response.json()

            if "items" in stats_data and "items" in channel_data:
                stats = {item["id"]: item for item in stats_data["items"]}
                channels = {item["id"]: item["statistics"] for item in channel_data["items"]}

                # Collect results
                for video in videos:
                    video_id = video["id"]["videoId"]
                    channel_id = video["snippet"]["channelId"]
                    title = video["snippet"].get("title", "N/A")
                    description = video["snippet"].get("description", "")[:200]
                    video_url = f"https://www.youtube.com/watch?v={video_id}"
                    views = int(stats.get(video_id, {}).get("statistics", {}).get("viewCount", 0))
                    subs = int(channels.get(channel_id, {}).get("subscriberCount", 0))

                    # Extract and parse video duration
                    duration_str = stats.get(video_id, {}).get("contentDetails", {}).get("duration", "PT0S")
                    duration_seconds = isodate.parse_duration(duration_str).total_seconds()

                    # Apply filters (views, subscribers, and duration > 1 minute)
                    if subs < 3000 and views >= min_views and duration_seconds >= 60:
                        all_results.append({
                            "Title": title,
                            "Description": description,
                            "URL": video_url,
                            "Views": views,
                            "Subscribers": subs,
                            "Duration (min)": round(duration_seconds / 60, 2)
                        })

        # Display results
        if all_results:
            st.success(f"Found {len(all_results)} trending videos!")
            for result in sorted(all_results, key=lambda x: x["Views"], reverse=True):  # Sort by views
                st.markdown(
                    f"**Title:** {result['Title']}  \n"
                    f"**Description:** {result['Description']}  \n"
                    f"**URL:** [Watch Video]({result['URL']})  \n"
                    f"**Views:** {result['Views']}  \n"
                    f"**Subscribers:** {result['Subscribers']}  \n"
                    f"**Duration:** {result['Duration (min)']} min"
                )
                st.write("---")
        else:
            st.warning("No results found with the given filters.")

    except Exception as e:
        st.error(f"An error occurred: {e}")
