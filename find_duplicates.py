import os
import hashlib
import logging
from pathlib import Path
from collections import defaultdict

# Configuration
# Add extensions you want to check. Empty set means check ALL files.
MEDIA_EXTENSIONS = {
    '.jpg', '.jpeg', '.png', '.tiff', '.webp', '.heic',  # Photos
    '.mp4', '.mov', '.avi', '.mkv', '.wmv', '.3gp'       # Videos
}

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def calculate_hash(file_path, block_size=65536, partial=False):
    """Calculates the MD5 hash of a file. If partial=True, only hashes the first 128KB."""
    hasher = hashlib.md5()
    try:
        with open(file_path, 'rb') as f:
            if partial:
                buf = f.read(128 * 1024) # Read first 128KB
                hasher.update(buf)
            else:
                buf = f.read(block_size)
                while len(buf) > 0:
                    hasher.update(buf)
                    buf = f.read(block_size)
        return hasher.hexdigest()
    except Exception as e:
        logging.error(f"Could not hash {file_path}: {e}")
        return None

def find_duplicates(root_dir, check_extensions_only=True, delete=False):
    root_path = Path(root_dir)
    if not root_path.exists():
        logging.error(f"Directory {root_dir} does not exist.")
        return

    # Phase 1: Group files by their size
    size_groups = defaultdict(list)
    
    logging.info(f"Scanning {root_dir} for files...")
    file_count = 0
    for file_path in root_path.rglob('*'):
        if not file_path.is_file():
            continue
            
        if check_extensions_only and file_path.suffix.lower() not in MEDIA_EXTENSIONS:
            continue
            
        try:
            size_groups[file_path.stat().st_size].append(file_path)
            file_count += 1
        except Exception as e:
            logging.error(f"Could not access {file_path}: {e}")

    # Process only groups with more than 1 file
    potential_duplicate_groups = [paths for paths in size_groups.values() if len(paths) > 1]
    
    if not potential_duplicate_groups:
        logging.info("No duplicates found (all file sizes are unique).")
        return

    # Phase 2: Fast Hash (Partial)
    # Most files with same size aren't actually duplicates. 
    # Hashing just the start of the file eliminates 99% of non-matches quickly.
    logging.info(f"Phase 2: Fast-hashing {len(potential_duplicate_groups)} size-collision groups...")
    
    partial_hash_groups = defaultdict(list)
    for group in potential_duplicate_groups:
        for path in group:
            p_hash = calculate_hash(path, partial=True)
            if p_hash:
                # Combine size and partial hash to ensure unique grouping
                key = (path.stat().st_size, p_hash)
                partial_hash_groups[key].append(path)

    # Filter to groups that still have multiple files after partial hashing
    final_contenders = [paths for paths in partial_hash_groups.values() if len(paths) > 1]
    
    if not final_contenders:
        logging.info("No actual duplicates found after fast-hash check.")
        return

    # Phase 3: Full Hash (Deep check)
    logging.info(f"Phase 3: Deep-hashing {len(final_contenders)} remaining potential duplicate groups...")
    
    duplicates = defaultdict(list)
    for i, group in enumerate(final_contenders):
        if (i + 1) % 100 == 0 or i == 0:
            logging.info(f"  Progress: Processing group {i+1}/{len(final_contenders)}...")
            
        for path in group:
            f_hash = calculate_hash(path, partial=False)
            if f_hash:
                duplicates[f_hash].append(path)

    # Phase 4: Reporting & Deletion
    found_any = False
    print("\n" + "="*50)
    print("DUPLICATE REPORT")
    print("="*50)
    
    deleted_count = 0
    total_space_saved = 0

    for file_hash, paths in duplicates.items():
        if len(paths) > 1:
            found_any = True
            # Sort paths to have a consistent "original" (e.g., first alphabetically)
            paths.sort()
            original = paths[0]
            dups = paths[1:]
            
            print(f"\n[MD5: {file_hash}]")
            print(f"  KEEP: {original}")
            
            for dup in dups:
                if delete:
                    try:
                        file_size = dup.stat().st_size
                        dup.unlink()
                        print(f"  DELETED: {dup}")
                        deleted_count += 1
                        total_space_saved += file_size
                    except Exception as e:
                        print(f"  ERROR DELETING {dup}: {e}")
                else:
                    print(f"  DUPLICATE: {dup}")
    
    if not found_any:
        print("\nNo identical files found.")
    else:
        unique_dup_files = sum(1 for paths in duplicates.values() if len(paths) > 1)
        print(f"\nSummary: Found duplicates for {unique_dup_files} unique files.")
        if delete:
            print(f"Action: Deleted {deleted_count} duplicate files.")
            print(f"Space Saved: {total_space_saved / (1024*1024):.2f} MB")
        else:
            print("Action: No files were deleted (use --delete to remove them).")
    print("="*50 + "\n")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Identify and optionally delete duplicate files based on content (MD5 hash).")
    parser.add_argument("directory", nargs="?", default=".", help="Directory to scan (defaults to current directory)")
    parser.add_argument("--all", action="store_true", help="Check ALL file types (not just photos/videos)")
    parser.add_argument("--delete", action="store_true", help="Actually delete the duplicate files (keeps the one with the first alphabetical path)")
    
    args = parser.parse_args()
    
    find_duplicates(args.directory, not args.all, args.delete)
    logging.info("Duplicate detection complete.")

