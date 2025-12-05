"""
Fireflies API Client
Fetches transcripts from Fireflies.ai using their GraphQL API
"""

import os
import requests
from datetime import datetime
from typing import List, Dict, Optional
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class FirefliesClient:
    """Client for interacting with Fireflies.ai API"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Fireflies client
        
        Args:
            api_key: Fireflies API key. If not provided, will look for FIREFLIES_API_KEY env var
        """
        self.api_key = api_key or os.getenv('FIREFLIES_API_KEY')
        if not self.api_key:
            raise ValueError("Fireflies API key not provided. Set FIREFLIES_API_KEY environment variable.")
        
        self.api_url = "https://api.fireflies.ai/graphql"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def get_transcripts(self, limit: int = 10, skip: int = 0) -> List[Dict]:
        """
        Get a list of transcripts from Fireflies
        
        Args:
            limit: Number of transcripts to fetch (default: 10)
            skip: Number of transcripts to skip for pagination (default: 0)
        
        Returns:
            List of transcript dictionaries
        """
        query = """
        query GetTranscripts($limit: Int, $skip: Int) {
            transcripts(limit: $limit, skip: $skip) {
                id
                title
                date
                duration
                meeting_attendees {
                    displayName
                    email
                }
                summary {
                    keywords
                    action_items
                    outline
                    shorthand_bullet
                    overview
                    bullet_gist
                }
                sentences {
                    text
                    speaker_name
                    start_time
                    end_time
                }
            }
        }
        """
        
        variables = {
            "limit": limit,
            "skip": skip
        }
        
        response = requests.post(
            self.api_url,
            json={"query": query, "variables": variables},
            headers=self.headers
        )
        
        if response.status_code != 200:
            raise Exception(f"API request failed: {response.status_code} - {response.text}")
        
        data = response.json()
        if 'errors' in data:
            raise Exception(f"GraphQL errors: {data['errors']}")
        
        return data.get('data', {}).get('transcripts', [])
    
    def get_transcript_by_id(self, transcript_id: str) -> Dict:
        """
        Get a specific transcript by ID
        
        Args:
            transcript_id: The ID of the transcript to fetch
        
        Returns:
            Transcript dictionary
        """
        query = """
        query GetTranscript($transcriptId: String!) {
            transcript(id: $transcriptId) {
                id
                title
                date
                duration
                audio_url
                video_url
                meeting_attendees {
                    displayName
                    email
                    phoneNumber
                }
                summary {
                    keywords
                    action_items
                    outline
                    shorthand_bullet
                    overview
                    bullet_gist
                }
                sentences {
                    text
                    speaker_name
                    start_time
                    end_time
                }
            }
        }
        """
        
        variables = {
            "transcriptId": transcript_id
        }
        
        response = requests.post(
            self.api_url,
            json={"query": query, "variables": variables},
            headers=self.headers
        )
        
        if response.status_code != 200:
            raise Exception(f"API request failed: {response.status_code} - {response.text}")
        
        data = response.json()
        if 'errors' in data:
            raise Exception(f"GraphQL errors: {data['errors']}")
        
        return data.get('data', {}).get('transcript', {})
    
    def search_transcripts(self, search_query: str, limit: int = 10) -> List[Dict]:
        """
        Search transcripts by query
        
        Args:
            search_query: Search query string
            limit: Number of results to return
        
        Returns:
            List of matching transcripts
        """
        query = """
        query SearchTranscripts($search: String, $limit: Int) {
            transcripts(search: $search, limit: $limit) {
                id
                title
                date
                duration
                meeting_attendees {
                    displayName
                    email
                }
                summary {
                    overview
                }
            }
        }
        """
        
        variables = {
            "search": search_query,
            "limit": limit
        }
        
        response = requests.post(
            self.api_url,
            json={"query": query, "variables": variables},
            headers=self.headers
        )
        
        if response.status_code != 200:
            raise Exception(f"API request failed: {response.status_code} - {response.text}")
        
        data = response.json()
        if 'errors' in data:
            raise Exception(f"GraphQL errors: {data['errors']}")
        
        return data.get('data', {}).get('transcripts', [])


def main():
    """Example usage of the Fireflies client"""
    try:
        # Initialize client
        client = FirefliesClient()
        
        print("=== Fireflies Transcript Fetcher ===\n")
        
        # Get recent transcripts
        print("Fetching recent transcripts...")
        transcripts = client.get_transcripts(limit=20)  # Get more to see date range
        
        if not transcripts:
            print("No transcripts found.")
            return
        
        print(f"\nFound {len(transcripts)} transcripts:\n")
        
        # Display transcript summaries
        for i, transcript in enumerate(transcripts, 1):
            print(f"{i}. Title: {transcript.get('title', 'Untitled')}")
            
            # Convert timestamp to readable date
            date_value = transcript.get('date', 'Unknown')
            if date_value != 'Unknown' and isinstance(date_value, (int, float)):
                # Fireflies returns timestamp in milliseconds
                date_obj = datetime.fromtimestamp(date_value / 1000)
                formatted_date = date_obj.strftime('%Y-%m-%d')
                print(f"   Date: {formatted_date}")
            else:
                print(f"   Date: {date_value}")
            
            duration_seconds = transcript.get('duration', 0)
            duration_minutes = duration_seconds / 60
            print(f"   Duration: {duration_minutes:.1f} minutes")
            print(f"   ID: {transcript.get('id', 'Unknown')}")
            print()
        
        # Save to JSON file
        output_file = f"fireflies_transcripts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w') as f:
            json.dump(transcripts, f, indent=2)
        print(f"Saved full transcript data to {output_file}")
        
        # Show date range summary
        if transcripts:
            dates = []
            for t in transcripts:
                date_val = t.get('date')
                if date_val and isinstance(date_val, (int, float)):
                    dates.append(datetime.fromtimestamp(date_val / 1000))
            
            if dates:
                oldest_date = min(dates)
                newest_date = max(dates)
                print(f"\nDate range: {oldest_date.strftime('%Y-%m-%d')} to {newest_date.strftime('%Y-%m-%d')}")
                print(f"Total span: {(newest_date - oldest_date).days} days")
        
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    main()