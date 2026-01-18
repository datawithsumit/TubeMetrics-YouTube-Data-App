import streamlit as st
import pandas as pd
from googleapiclient.discovery import build

API_KEY = 'YOUR_API_KEY'  

YOUTUBE_API_SERVICE_NAME = 'youtube'
YOUTUBE_API_VERSION = 'v3'

st.set_page_config(page_title="TubeMetrics", page_icon="Hz", layout="wide")

def get_channel_stats(youtube, channel_id):
    """Fetch channel statistics and the 'Uploads' playlist ID."""
    request = youtube.channels().list(
        part='snippet,contentDetails,statistics',
        id=channel_id
    )
    response = request.execute()
    
    if response['items']:
        data = response['items'][0]
        return {
            'channel_name': data['snippet']['title'],
            'subscribers': data['statistics']['subscriberCount'],
            'views': data['statistics']['viewCount'],
            'total_videos': data['statistics']['videoCount'],
            'playlist_id': data['contentDetails']['relatedPlaylists']['uploads'],
            'thumbnail': data['snippet']['thumbnails']['high']['url']
        }
    return None

def get_video_ids(youtube, playlist_id):
    """Fetch the list of video IDs from the Uploads playlist."""
    request = youtube.playlistItems().list(
        part='snippet',  
        playlistId=playlist_id,
        maxResults=50
    )
    response = request.execute()
    
    video_ids = []
    for item in response['items']:
        video_ids.append(item['snippet']['resourceId']['videoId'])
    
    return video_ids

def get_video_details(youtube, video_ids):
    """Fetch detailed stats (Views, Likes) for the list of videos."""
    if not video_ids:
        return []
        
    request = youtube.videos().list(
        part='snippet,statistics',
        id=','.join(video_ids)
    )
    response = request.execute()
    
    video_stats = []
    for video in response['items']:
        stats = video['statistics']
        snippet = video['snippet']
        
        video_stats.append({
            'Title': snippet['title'],
            'Published_Date': snippet['publishedAt'],
            'Views': int(stats.get('viewCount', 0)),
            'Likes': int(stats.get('likeCount', 0)),
            'Comments': int(stats.get('commentCount', 0)),
            'Thumbnail': snippet['thumbnails']['default']['url']
        })
    
    return video_stats

st.title("🎥 TubeMetrics: Viral Strategy Analyzer")
st.write("Compare the last 50 videos to find viral patterns.")

# Initialize API
try:
    youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=API_KEY)

    with st.sidebar:
        st.header("Search Settings")
        channel_id = st.text_input("Enter Channel ID:", "UCX6OQ3DkcsbYNE6H8uQQuVA")
        submit_button = st.button("Analyze Channel")

    if submit_button:
        channel_data = get_channel_stats(youtube, channel_id)
        
        if channel_data:
            col1, col2 = st.columns([1, 4])
            with col1:
                st.image(channel_data['thumbnail'], width=150)
            with col2:
                st.title(channel_data['channel_name'])
                st.metric("Subscribers", f"{int(channel_data['subscribers']):,}")
                st.metric("Total Views", f"{int(channel_data['views']):,}")

            st.divider()
        
            with st.spinner('Fetching latest 50 videos...'):
                video_ids = get_video_ids(youtube, channel_data['playlist_id'])
                video_details = get_video_details(youtube, video_ids)
            
                df = pd.DataFrame(video_details)
                
                if not df.empty:
                    df['Published_Date'] = pd.to_datetime(df['Published_Date']).dt.date
                    
                    st.subheader("📺 Recent Video Performance")
                    st.dataframe(df, use_container_width=True)
                else:
                    st.warning("No videos found in this channel's upload list.")
                
                st.divider()
                st.subheader("📈 Viral Metrics Analysis")

                st.write("**Views per Video (Last 50 Uploads)**")
                st.bar_chart(df, x="Published_Date", y="Views")

                st.write("**Engagement Check: Do higher views mean more likes?**")
                st.scatter_chart(df, x="Views", y="Likes")

                st.divider()
                st.subheader("💾 Download Data")
                
                csv = df.to_csv(index=False).encode('utf-8')
                
                st.download_button(
                    label="Download Data as CSV",
                    data=csv,
                    file_name=f"{channel_data['channel_name']}_data.csv",
                    mime="text/csv",
                )
        else:
            st.error("Channel not found! Please check the ID.")
        

except Exception as e:
    st.error(f"An error occurred: {e}")