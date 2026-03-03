import os
import subprocess
import logging
from pathlib import Path

# Configuration
MEDIA_EXTENSIONS = {
    '.jpg', '.jpeg', '.png', '.tiff', '.webp', '.heic',  # Photos
    '.mp4', '.mov', '.avi', '.mkv', '.wmv', '.3gp'       # Videos
}

# Automatically find exiftool.exe in the same folder as this script
SCRIPT_DIR = Path(__file__).parent.absolute()
EXIFTOOL_PATH = SCRIPT_DIR / "exiftool.exe"

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def update_metadata_in_directory(directory, date_string):
    """Updates all media files in a directory using exiftool."""
    logging.info(f"Updating contents of '{directory}' to date: {date_string}")
    
    # We target common media extensions
    # -AllDates updates DateTimeOriginal, CreateDate, and ModifyDate
    # -overwrite_original avoids creating .original backup files
    cmd = [
        EXIFTOOL_PATH,
        f"-AllDates={date_string}",
        "-overwrite_original",
        "." # Apply to all files in THIS directory
    ]
    
    try:
        # Run exiftool within the specific folder
        result = subprocess.run(cmd, cwd=directory, capture_output=True, text=True)
        if result.returncode == 0:
            logging.info(f"Successfully updated {directory}")
            print(result.stdout)
        else:
            logging.error(f"Error updating {directory}: {result.stderr}")
    except Exception as e:
        logging.error(f"Failed to run exiftool in {directory}: {e}")

def walk_and_update(root_dir):
    root_path = Path(root_dir)
    
    if not root_path.exists():
        logging.error(f"Root directory {root_dir} does not exist.")
        return

    # Check root directory first, then subdirectories
    directories = [root_path] + [p for p in root_path.rglob('*') if p.is_dir()]
    
    for folder in directories:
        date_file = folder / "date.txt"
        
        if date_file.exists():
            try:
                # Read the date string from date.txt
                with open(date_file, 'r') as f:
                    date_string = f.read().strip()
                
                if date_string:
                    update_metadata_in_directory(folder, date_string)
                else:
                    logging.warning(f"Skipping {folder}: date.txt is empty.")
                    
            except Exception as e:
                logging.error(f"Error reading {date_file}: {e}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Update EXIF dates using date.txt in subfolders.")
    parser.add_argument("directory", nargs="?", default=".", help="Root directory to scan (defaults to current directory)")
    
    args = parser.parse_args()
    
    # If the EXIFTOOL_PATH doesn't exist, try just "exiftool" (assuming it's in PATH)
    if not os.path.exists(EXIFTOOL_PATH):
        logging.warning(f"ExifTool not found at specified path: {EXIFTOOL_PATH}")
        logging.info("Falling back to 'exiftool' command...")
        EXIFTOOL_PATH = "exiftool"

    walk_and_update(args.directory)
    logging.info("Metadata update process complete.")
