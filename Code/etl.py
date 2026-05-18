import json
import logging
from pathlib import Path
import pandas as pd
import networkx as nx
import re

# Configure robust logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("etl_processing.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"

INPUT_PROFILES_FILE = DATA_DIR / "raw_profiles.json"
INPUT_POSTS_FILE = DATA_DIR / "raw_posts.json"
OUTPUT_NODES_CSV = DATA_DIR / "nodes.csv"
OUTPUT_EDGES_CSV = DATA_DIR / "edges.csv"
OUTPUT_POSTS_CSV = DATA_DIR / "posts.csv"
OUTPUT_GRAPHML = DATA_DIR / "network.graphml"

def extract_hashtags(text):
    if not text:
        return ""
    # Find all hashtags and return them as a comma-separated string
    hashtags = re.findall(r'#\w+', text)
    return ", ".join(hashtags)

def process_profiles():
    if not INPUT_PROFILES_FILE.exists():
        logger.warning(f"Profiles data not found at {INPUT_PROFILES_FILE}. Skipping profile processing.")
        return pd.DataFrame()
        
    with open(INPUT_PROFILES_FILE, 'r') as f:
        raw_profiles = json.load(f)
        
    processed = []
    for p in raw_profiles:
        bio = p.get("biography", "")
        # Try to parse address if it exists as a JSON string
        address = ""
        if p.get("businessAddressJson"):
            try:
                addr_data = json.loads(p.get("businessAddressJson"))
                address = f"{addr_data.get('city_name', '')}, {addr_data.get('region_name', '')}".strip(', ')
            except (json.JSONDecodeError, TypeError):
                pass
                
        processed.append({
            "id": p.get("username"),
            "full_name": p.get("fullName"),
            "biography": bio,
            "bio_hashtags": extract_hashtags(bio),
            "followers": p.get("followersCount"),
            "following": p.get("followsCount"),
            "posts_count": p.get("postsCount"),
            "external_url": p.get("externalUrl"),
            "geo_location": address,
            "category": p.get("businessCategoryName", ""),
            "is_verified": p.get("isVerified")
        })
        
    df = pd.DataFrame(processed)
    df = df.dropna(subset=['id'])
    
    df.to_csv(OUTPUT_NODES_CSV, index=False)
    logger.info(f"Saved {len(df)} profile nodes to {OUTPUT_NODES_CSV}")
    return df

def process_posts():
    if not INPUT_POSTS_FILE.exists():
        logger.warning(f"Posts data not found at {INPUT_POSTS_FILE}. Skipping post processing.")
        return pd.DataFrame(), pd.DataFrame()
        
    with open(INPUT_POSTS_FILE, 'r') as f:
        raw_posts = json.load(f)
        
    edges = []
    post_records = []
    
    for post in raw_posts:
        source = post.get("ownerUsername")
        if not source:
            continue
            
        timestamp = post.get("timestamp")
        post_url = post.get("url")
        caption = post.get("caption", "")
        
        # Save post metadata for Natalia's 'date posted' and 'hashtag' requirements
        post_records.append({
            "username": source,
            "post_url": post_url,
            "date_posted": timestamp,
            "likes": post.get("likesCount"),
            "comments": post.get("commentsCount"),
            "post_hashtags": extract_hashtags(caption)
        })
            
        mentions = post.get("mentions", [])
        if not mentions:
            continue
        
        for target in mentions:
            if target != source:
                edges.append({
                    "source": source,
                    "target": target,
                    "weight": 1,
                    "timestamp": timestamp,
                    "post_url": post_url
                })
                
    edges_df = pd.DataFrame(edges)
    posts_df = pd.DataFrame(post_records)
    
    if not posts_df.empty:
        posts_df.to_csv(OUTPUT_POSTS_CSV, index=False)
        logger.info(f"Saved {len(posts_df)} posts metadata to {OUTPUT_POSTS_CSV}")
        
    if not edges_df.empty:
        weighted_edges = edges_df.groupby(["source", "target"]).size().reset_index(name="weight")
        weighted_edges.to_csv(OUTPUT_EDGES_CSV, index=False)
        logger.info(f"Saved {len(weighted_edges)} aggregated edges to {OUTPUT_EDGES_CSV}")
        return weighted_edges, posts_df
    else:
        logger.warning("No edges (mentions) found in posts data.")
        return pd.DataFrame(), posts_df

def create_network_graph(nodes_df, edges_df):
    G = nx.DiGraph()
    
    if not nodes_df.empty:
        for row_dict in nodes_df.to_dict('records'):
            # Drop NaN values by filtering the dict
            clean_row = {k: v for k, v in row_dict.items() if pd.notna(v)}
            G.add_node(clean_row['id'], **clean_row)
            
    if not edges_df.empty:
        for row_dict in edges_df.to_dict('records'):
            G.add_edge(row_dict['source'], row_dict['target'], weight=row_dict['weight'])
            
    if len(G.nodes) > 0:
        nx.write_graphml(G, OUTPUT_GRAPHML)
        logger.info(f"Saved GraphML to {OUTPUT_GRAPHML} with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges.")
    else:
        logger.warning("Graph is empty. GraphML not created.")

def create_client_summary(nodes_df, posts_df):
    if nodes_df.empty:
        return
        
    summary_records = []
    for _, row in nodes_df.iterrows():
        username = row['id']
        
        # Gather dates posted from posts_df for this user
        recent_dates = []
        if not posts_df.empty:
            user_posts = posts_df[posts_df['username'] == username]
            recent_dates = user_posts['date_posted'].dropna().tolist()
            # formatting dates to simple YYYY-MM-DD
            recent_dates = [d.split('T')[0] for d in recent_dates if isinstance(d, str)]
            
        summary_records.append({
            "Instagram Handle": username,
            "Bio": row['biography'],
            "Geo Location": row['geo_location'] if row['geo_location'] else "Not Provided",
            "Followers": row['followers'],
            "Following": row['following'],
            "Year Joined": "N/A (Requires deep historical scrape)",
            "Total Number of Posts": row['posts_count'],
            "Dates of Recent Posts": ", ".join(recent_dates),
            "Bio Hashtags": row['bio_hashtags'],
            "Website/Links in Bio": row['external_url']
        })
        
    summary_df = pd.DataFrame(summary_records)
    output_path = DATA_DIR / "client_export.csv"
    summary_df.to_csv(output_path, index=False)
    logger.info(f"Saved {len(summary_df)} rows to {output_path} specifically for Natalia's request.")

def main():
    logger.info("Starting ETL processing.")
    
    nodes_df = process_profiles()
    edges_df, posts_df = process_posts()
    
    create_network_graph(nodes_df, edges_df)
    create_client_summary(nodes_df, posts_df)
    
    logger.info("ETL processing complete.")

if __name__ == "__main__":
    main()
