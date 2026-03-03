import os
import logging
from pathlib import Path

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def rename_mp_to_mp4(directory):
    root_path = Path(directory)
    if not root_path.exists():
        logging.error(f"Directory {directory} does not exist.")
        return

    logging.info(f"Scanning {directory} for .mp files...")
    
    count = 0
    for file_path in root_path.rglob('*.mp'):
        if file_path.is_file():
            new_path = file_path.with_suffix('.mp4')
            
            # Check if target already exists
            if new_path.exists():
                logging.warning(f"Cannot rename {file_path} because {new_path} already exists.")
                continue
                
            try:
                file_path.rename(new_path)
                logging.info(f"Renamed: {file_path.name} -> {new_path.name}")
                count += 1
            except Exception as e:
                logging.error(f"Failed to rename {file_path}: {e}")

    logging.info(f"Finished. Renamed {count} files.")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Recursively rename all .mp files to .mp4.")
    parser.add_argument("directory", nargs="?", default=".", help="Directory to scan (defaults to current directory)")
    
    args = parser.parse_args()
    rename_mp_to_mp4(args.directory)
