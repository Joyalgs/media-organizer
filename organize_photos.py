import os
import logging
import datetime
from pathlib import Path
from PIL import Image
from PIL.ExifTags import TAGS
from pillow_heif import register_heif_opener
from hachoir.parser import createParser
from hachoir.metadata import extractMetadata

register_heif_opener()

# Configuration
SOURCE_EXTENSIONS = {
    'photos': {'.jpg', '.jpeg', '.png', '.tiff', '.webp', '.heic'},
    'videos': {'.mp4', '.mov', '.avi', '.mkv', '.wmv', '.3gp'}
}

IGNORE_EXTENSIONS = {'.json', '.ini', '.db', '.DS_Store', '.txt'}


LOG_FILE = "photo_organizer.log"

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

def get_photo_metadata_timestamp(file_path):
    """Extracts date taken from photo EXIF data (Priority 1)."""
    try:
        with Image.open(file_path) as img:
            exif_data = img._getexif()
            if exif_data:
                # Try DateTimeOriginal first, then DateTimeDigitized
                for tag_to_find in ['DateTimeOriginal', 'DateTimeDigitized']:
                    for tag, value in exif_data.items():
                        tag_name = TAGS.get(tag, tag)
                        if tag_name == tag_to_find and value:
                            try:
                                parsed_date = datetime.datetime.strptime(str(value), '%Y:%m:%d %H:%M:%S')
                                # Ignore placeholder dates (e.g., 0000:00:00) or very early dates
                                if parsed_date.year > 1900:
                                    return parsed_date
                            except ValueError:
                                continue
    except Exception as e:
        logging.debug(f"Could not extract EXIF metadata from {file_path}: {e}")
    return None

def get_video_metadata_timestamp(file_path):
    """Extracts creation date from video metadata (Priority 1)."""
    try:
        parser = createParser(str(file_path))
        if not parser:
            return None
        with parser:
            metadata = extractMetadata(parser)
            if metadata:
                creation_date = metadata.get('creation_date')
                if creation_date:
                    # Check for the common "66-year shift" bug in QuickTime/MP4 files.
                    # This happens when a Unix timestamp (since 1970) is incorrectly 
                    # stored in a field expecting an MP4 timestamp (since 1904).
                    if 1904 < creation_date.year < 1970:
                        try:
                            # Add 66 years to correct the shift (e.g., 1948 -> 2014)
                            corrected_date = creation_date.replace(year=creation_date.year + 66)
                            logging.info(f"Fixed 66-year shift for {file_path}: {creation_date} -> {corrected_date}")
                            return corrected_date
                        except ValueError:
                            # Handle Feb 29 edge cases
                            return creation_date + datetime.timedelta(days=66*365 + 16)
                    
                    # Ignore exact 1904 epoch (often a zero/placeholder)
                    if creation_date.year > 1904:
                        return creation_date
    except Exception as e:
        logging.debug(f"Could not extract video metadata from {file_path}: {e}")
    return None

def get_timestamp(file_path):
    """
    Attempts to get timestamp based on priorities:
    1. EXIF Metadata (Date Taken)
    2. Upload Date (interpreted as File Creation Time)
    3. File Modification Date
    """
    suffix = file_path.suffix.lower()
    
    # Priority 1: EXIF Metadata
    metadata_ts = None
    if suffix in SOURCE_EXTENSIONS['photos']:
        metadata_ts = get_photo_metadata_timestamp(file_path)
    elif suffix in SOURCE_EXTENSIONS['videos']:
        metadata_ts = get_video_metadata_timestamp(file_path)
    
    if metadata_ts:
        logging.debug(f"Using Priority 1 (Metadata) for {file_path}")
        return metadata_ts

    # Priority 2: Upload Date (File Creation Time)
    # On Windows, st_ctime is the creation time.
    try:
        stat = file_path.stat()
        creation_time = datetime.datetime.fromtimestamp(stat.st_ctime)
        logging.info(f"Metadata missing for {file_path}. Using Priority 2 (Upload Date/Creation Time): {creation_time}")
        return creation_time
    except Exception as e:
        logging.debug(f"Could not get creation time for {file_path}: {e}")

    # Priority 3: File Modification Date
    try:
        stat = file_path.stat()
        mod_time = datetime.datetime.fromtimestamp(stat.st_mtime)
        logging.info(f"Metadata and Creation time missing for {file_path}. Using Priority 3 (Modification Time): {mod_time}")
        return mod_time
    except Exception as e:
        logging.error(f"Could not determine any date for {file_path}: {e}")
        return None

def organize_files(source_dir, target_dir):
    source_path = Path(source_dir)
    target_path = Path(target_dir)
    
    if not source_path.exists():
        logging.error(f"Source directory {source_dir} does not exist.")
        return

    # To track counts per timestamp for sequence suffix
    timestamp_counts = {}

    # Define review folder
    review_dir = target_path / "review"

    for file_path in source_path.rglob('*'):
        if file_path.is_dir():
            continue

        if file_path.suffix.lower() in IGNORE_EXTENSIONS:
            logging.info(f"Skipping ignored file: {file_path}")
            continue

        try:
            timestamp = get_timestamp(file_path)
            if not timestamp:
                raise ValueError("No valid date metadata or file timestamps found.")
            year = timestamp.strftime('%Y')
            month = timestamp.strftime('%m')
            timestamp_str = timestamp.strftime('%Y%m%d%H%M%S')
            
            # Create year/month directory
            dest_dir = target_path / year / month
            dest_dir.mkdir(parents=True, exist_ok=True)
            
            # Handle sequence numbering
            count = timestamp_counts.get(timestamp_str, 0) + 1
            timestamp_counts[timestamp_str] = count
            
            # Keep original extension
            ext = file_path.suffix.lower() if file_path.suffix else ""
            new_filename = f"{timestamp_str}_{count:02d}{ext}"
            final_path = dest_dir / new_filename
            
            # If the file already exists (unlikely with timestamp + sequence, but for safety),
            # we check if we need to increment further
            while final_path.exists():
                count += 1
                new_filename = f"{timestamp_str}_{count:02d}{ext}"
                final_path = dest_dir / new_filename
            
            # Move and log
            logging.info(f"Moving: {file_path} -> {final_path}")
            import shutil
            shutil.move(str(file_path), str(final_path))
            
        except Exception as e:
            logging.error(f"Error processing {file_path}: {e}")
            try:
                # Move to review folder on error
                review_dir.mkdir(parents=True, exist_ok=True)
                
                # Generate a unique filename for review: OriginalName_YYYYMMDD_HHMMSS_UUID.ext
                import uuid
                now_str = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                unique_suffix = uuid.uuid4().hex[:8]
                review_filename = f"{file_path.stem}_{now_str}_{unique_suffix}{file_path.suffix}"
                review_dest = review_dir / review_filename
                
                logging.warning(f"Moving problematic file to review: {file_path} -> {review_dest}")
                import shutil
                shutil.move(str(file_path), str(review_dest))
            except Exception as move_error:
                logging.error(f"Failed to move {file_path} to review folder: {move_error}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Organize photos and videos by date.")
    parser.add_argument("source", help="Source directory to scan")
    parser.add_argument("target", help="Target directory for organized files")
    
    args = parser.parse_args()
    
    organize_files(args.source, args.target)
    logging.info("Organization complete.")
