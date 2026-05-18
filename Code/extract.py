import os
import sys
import json
import logging
from pathlib import Path
from dotenv import load_dotenv
from apify_client import ApifyClient
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type
import concurrent.futures

# Configure robust logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("apify_extraction.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN")

if not APIFY_API_TOKEN:
    logger.error("APIFY_API_TOKEN is missing. Please set it in the .env file.")
    sys.exit(1)

MAX_POSTS_PER_PROFILE = int(os.getenv("MAX_POSTS_PER_PROFILE", 5))

# Initialize Apify Client
client = ApifyClient(APIFY_API_TOKEN)

# Define file paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

TARGET_FILE = BASE_DIR / "target_profiles.json"
OUTPUT_PROFILES_FILE = DATA_DIR / "raw_profiles.json"
OUTPUT_POSTS_FILE = DATA_DIR / "raw_posts.json"

@retry(
    wait=wait_exponential(multiplier=1, min=4, max=60), 
    stop=stop_after_attempt(3),
    retry=retry_if_exception_type(Exception)
)
def run_apify_actor(actor_id: str, run_input: dict) -> list:
    """
    Runs an Apify actor with retry logic and returns the dataset items.
    """
    logger.info(f"Starting actor {actor_id} with input: {run_input}")
    try:
        # Start the actor and wait for it to finish
        actor_call = client.actor(actor_id).call(run_input=run_input)
        dataset_id = actor_call.get("defaultDatasetId")
        
        if not dataset_id:
            logger.error(f"No dataset ID returned for {actor_id}")
            return []

        # Fetch the results from the dataset
        logger.info(f"Fetching dataset {dataset_id} for actor {actor_id}...")
        dataset = client.dataset(dataset_id)
        items = [item for item in dataset.iterate_items()]
        logger.info(f"Successfully retrieved {len(items)} items from {actor_id}.")
        return items
    except Exception as e:
        logger.error(f"Error running actor {actor_id}: {e}")
        raise

def main():
    logger.info("Starting Apify extraction pipeline.")
    
    # 1. Load targets
    if not TARGET_FILE.exists():
        logger.error(f"Target file not found at {TARGET_FILE}")
        return

    with open(TARGET_FILE, 'r') as f:
        targets = json.load(f)

    usernames = [t["instagram_handle"] for t in targets if t.get("instagram_handle")]
    logger.info(f"Loaded {len(usernames)} target handles.")

    if not usernames:
        logger.warning("No valid Instagram handles found in targets.")
        return

    # To maximize free credits, you can optionally chunk the usernames array here.
    # For 18 profiles, a single run is usually fine.
    
    profile_input = {
        "usernames": usernames,
        "includeAboutSection": False,
    }
    
    post_input = {
        "username": usernames,
        "resultsLimit": MAX_POSTS_PER_PROFILE, 
        "resultsType": "posts",
        "proxy_config": {
            "useApifyProxy": True
        }
    }

    logger.info("--- Extracting Profile Metadata & Recent Posts Concurrently ---")
    
    profiles_data, posts_data = None, None
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        future_profiles = executor.submit(run_apify_actor, "apify/instagram-profile-scraper", profile_input)
        future_posts = executor.submit(run_apify_actor, "apify/instagram-post-scraper", post_input)
        
        try:
            profiles_data = future_profiles.result()
        except Exception as e:
            logger.error(f"Profile extraction failed: {e}")
            
        try:
            posts_data = future_posts.result()
        except Exception as e:
            logger.error(f"Post extraction failed: {e}")
    
    if profiles_data:
        with open(OUTPUT_PROFILES_FILE, 'w') as f:
            json.dump(profiles_data, f, indent=2)
        logger.info(f"Saved profile metadata to {OUTPUT_PROFILES_FILE}")

    if posts_data:
        with open(OUTPUT_POSTS_FILE, 'w') as f:
            json.dump(posts_data, f, indent=2)
        logger.info(f"Saved post data to {OUTPUT_POSTS_FILE}")

    logger.info("Extraction pipeline complete. Check the data/ directory for outputs.")

if __name__ == "__main__":
    main()
