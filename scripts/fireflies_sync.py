#!/usr/bin/env python3
"""
Fetch recent Fireflies transcripts (newest first) and export as markdown files.
"""

import os
import re
from datetime import datetime

from fireflies_api import FirefliesClient
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()

def sanitize_filename(filename):
    """Sanitize filename for filesystem"""
    # Remove invalid characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Limit length
    if len(sanitized) > 200:
        sanitized = sanitized[:200]
    return sanitized.strip()


def _looks_like_header(line):
    if not line:
        return False
    stripped = line.strip()
    if re.match(r'^[-*•–]\s', stripped):
        return False
    # Treat lines containing bold markers as headers (handles emoji + **Title** cases)
    return bool(re.search(r'\*\*[^*].+?\*\*', stripped))


def _append_text_block(content, text, treat_headers=False):
    """Split multiline text into paragraphs and bullet each line for readability."""
    if not text:
        return
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    for paragraph in paragraphs:
        lines = [line.strip() for line in paragraph.splitlines() if line.strip()]
        if not lines:
            continue
        header = None
        if treat_headers:
            first_line = lines[0]
            stripped_first = re.sub(r'^[-*•–]\s+', '', first_line).strip()
            if _looks_like_header(stripped_first):
                header = stripped_first
                lines = lines[1:]
        if header:
            content.append(header)
        for line in lines:
            if re.match(r'^[-*•–]\s', line):
                content.append(line)
            else:
                content.append(f"- {line}")
        content.append("")


def append_block_from_value(content, value, treat_headers=False):
    """Append bullet-formatted content regardless of whether the source is a list or string."""
    if value is None:
        return
    if isinstance(value, list):
        for entry in value:
            append_block_from_value(content, entry, treat_headers=treat_headers)
    else:
        _append_text_block(content, str(value), treat_headers=treat_headers)

def create_markdown_file(transcript, output_dir):
    """Create a markdown file for a single transcript"""
    try:
        # Extract basic info
        title = transcript.get('title', 'Untitled')
        transcript_id = transcript.get('id', 'unknown')
        date_value = transcript.get('date')
        
        # Format date
        if date_value and isinstance(date_value, (int, float)):
            date_obj = datetime.fromtimestamp(date_value / 1000)
            formatted_date = date_obj.strftime('%Y-%m-%d %H:%M')
            file_date = date_obj.strftime('%Y-%m-%d')  # Changed to YYYY-MM-DD format
        else:
            formatted_date = 'Unknown'
            file_date = 'unknown-date'
        
        # Create filename
        safe_title = sanitize_filename(title)
        filename = f"{file_date}_{safe_title}_{transcript_id[:8]}.md"
        filepath = os.path.join(output_dir, filename)
        
        # Create markdown content
        content = []
        content.append(f"# {title}\n")
        content.append(f"**Date:** {formatted_date}  ")
        content.append(f"**ID:** {transcript_id}  ")
        
        # Duration
        duration_seconds = transcript.get('duration', 0)
        duration_minutes = duration_seconds / 60
        content.append(f"**Duration:** {duration_minutes:.1f} minutes  \n")
        
        # Meeting attendees
        attendees = transcript.get('meeting_attendees', [])
        if attendees:
            content.append("\n## Attendees\n")
            for attendee in attendees:
                name = attendee.get('displayName', '')
                email = attendee.get('email', '')
                phone = attendee.get('phoneNumber', '')
                
                attendee_info = []
                if name:
                    attendee_info.append(name)
                if email:
                    attendee_info.append(f"({email})")
                if phone:
                    attendee_info.append(f"- {phone}")
                
                if attendee_info:
                    content.append(f"- {' '.join(attendee_info)}")
            content.append("")
        
        # Summary section
        summary = transcript.get('summary', {})
        if summary:
            # Keywords
            keywords = summary.get('keywords')
            if keywords:
                content.append("\n## Keywords\n")
                if isinstance(keywords, list):
                    content.append(", ".join(keywords))
                else:
                    content.append(str(keywords))
                content.append("\n")
            
            # Overview
            overview = summary.get('overview')
            if overview:
                content.append("\n## Overview\n")
                content.append(overview)
                content.append("\n")
            
            # Action items
            action_items = summary.get('action_items')
            if action_items:
                content.append("\n## Action Items\n")
                append_block_from_value(content, action_items, treat_headers=True)

            # Outline
            outline = summary.get('outline')
            if outline:
                content.append("\n## Meeting Outline\n")
                if isinstance(outline, list):
                    for item in outline:
                        content.append(f"- {item}")
                else:
                    content.append(str(outline))
                content.append("\n")
            
            # Bullet points
            bullet_gist = summary.get('bullet_gist')
            if bullet_gist:
                content.append("\n## Key Points\n")
                append_block_from_value(content, bullet_gist)

            # Shorthand bullets
            shorthand = summary.get('shorthand_bullet')
            if shorthand:
                content.append("\n## Summary Bullets\n")
                append_block_from_value(content, shorthand, treat_headers=True)
        
        # Transcript sentences
        sentences = transcript.get('sentences', [])
        if sentences:
            content.append("\n## Full Transcript\n")
            
            # Sort sentences by start_time to ensure chronological order
            sorted_sentences = sorted(sentences, key=lambda x: x.get('start_time', 0))
            
            for sentence in sorted_sentences:
                speaker = sentence.get('speaker_name', 'Unknown')
                text = sentence.get('text', '')
                start_time = sentence.get('start_time', 0)
                
                # Convert milliseconds to MM:SS format
                minutes = int(start_time / 60000)
                seconds = int((start_time % 60000) / 1000)
                timestamp = f"{minutes:02d}:{seconds:02d}"
                
                # Each line shows: [timestamp] Speaker: text
                content.append(f"[{timestamp}] **{speaker}**: {text}  ")
            content.append("\n")
        
        # Audio/Video URLs
        audio_url = transcript.get('audio_url')
        video_url = transcript.get('video_url')
        
        if audio_url or video_url:
            content.append("\n## Media Links\n")
            if audio_url:
                content.append(f"- [Audio Recording]({audio_url})")
            if video_url:
                content.append(f"- [Video Recording]({video_url})")
            content.append("\n")
        
        # Write to file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('\n'.join(content))
        
        return filepath
        
    except Exception as e:
        print(f"Error creating markdown for transcript {transcript_id}: {e}")
        return None

def fetch_recent_transcripts(max_transcripts=10, batch_limit=10):
    """Fetch the newest transcripts and export them as markdown files."""
    try:
        client = FirefliesClient()

        print("=== Fetching Recent Fireflies Transcripts ===\n")

        output_dir = f"fireflies_transcripts_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        os.makedirs(output_dir, exist_ok=True)
        print(f"Created output directory: {output_dir}\n")

        collected_transcripts = []
        seen_ids = set()
        skip = 0
        batch_count = 0

        while len(collected_transcripts) < max_transcripts:
            batch_count += 1
            print(f"Fetching batch {batch_count}: skip={skip}, limit={batch_limit}...")

            try:
                batch = client.get_transcripts(limit=batch_limit, skip=skip)
            except Exception as e:
                print(f"Error fetching batch: {e}")
                print("Waiting 5 seconds before retry...")
                time.sleep(5)
                continue

            if not batch:
                print("No more transcripts found.")
                break

            batch_sorted = sorted(batch, key=lambda x: x.get('date', 0), reverse=True)
            batch_to_export = []

            for transcript in batch_sorted:
                transcript_id = transcript.get('id')
                if not transcript_id or transcript_id in seen_ids:
                    continue
                seen_ids.add(transcript_id)
                batch_to_export.append(transcript)
                collected_transcripts.append(transcript)
                if len(collected_transcripts) >= max_transcripts:
                    break

            print(f"  Found {len(batch)} transcripts in this batch")
            print(f"  {len(batch_to_export)} queued for export")
            print(f"  Total collected: {len(collected_transcripts)}/{max_transcripts}")

            if batch_to_export:
                print(f"  Creating markdown files for {len(batch_to_export)} transcripts...")
                for i, transcript in enumerate(batch_to_export, 1):
                    title = transcript.get('title', 'Untitled')
                    print(f"    [{i}/{len(batch_to_export)}] Exporting: {title[:50]}...")

                    try:
                        transcript_id = transcript.get('id')
                        if transcript_id:
                            full_transcript = client.get_transcript_by_id(transcript_id)
                            if full_transcript:
                                filepath = create_markdown_file(full_transcript, output_dir)
                                if filepath:
                                    print(f"      ✓ Saved: {os.path.basename(filepath)}")
                                else:
                                    print(f"      ✗ Failed to save")
                            else:
                                print(f"      ✗ Could not fetch full details")
                    except Exception as e:
                        print(f"      ✗ Error: {e}")

                    time.sleep(0.5)

            if len(collected_transcripts) >= max_transcripts:
                print(f"\nReached maximum of {max_transcripts} transcripts. Stopping.")
                break

            if len(batch) < batch_limit:
                print("\nReached end of available transcripts.")
                break

            skip += batch_limit

            print("\nWaiting 2 seconds before next batch...\n")
            time.sleep(2)

        print("\n" + "="*50)
        print(f"Total transcripts exported: {len(collected_transcripts)}")
        print(f"Markdown files created in: {output_dir}")

        index_path = os.path.join(output_dir, "index.md")
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write("# Fireflies Transcripts\n\n")
            f.write(f"Total transcripts: {len(collected_transcripts)}\n\n")

            collected_transcripts.sort(key=lambda x: x.get('date', 0), reverse=True)

            monthly = {}
            for t in collected_transcripts:
                date_val = t.get('date')
                if date_val:
                    date_obj = datetime.fromtimestamp(date_val / 1000)
                    month_key = date_obj.strftime('%B %Y')
                    monthly.setdefault(month_key, []).append(t)

            for month, transcripts in monthly.items():
                f.write(f"\n## {month}\n\n")
                for t in transcripts:
                    title = t.get('title', 'Untitled')
                    t_id = t.get('id', 'unknown')
                    date_val = t.get('date')
                    if date_val:
                        date_str = datetime.fromtimestamp(date_val / 1000).strftime('%Y-%m-%d')
                    else:
                        date_str = 'unknown'

                    safe_title = sanitize_filename(title)
                    file_date = datetime.fromtimestamp(date_val / 1000).strftime('%Y-%m-%d') if date_val else 'unknown-date'
                    filename = f"{file_date}_{safe_title}_{t_id[:8]}.md"

                    f.write(f"- [{date_str}] [{title}]({filename})\n")

        print(f"\nIndex created: {index_path}")
        print("\nDone!")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    fetch_recent_transcripts()
