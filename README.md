# 📸 Photo & Video Organizer

A robust Python utility designed to recursively scan directories and organize photos and videos based on their internal metadata timestamps (EXIF/Creation Date).

## 🚀 Overview

Tired of messy folders with filenames like `IMG_4821.JPG`? This script extracts the actual date the photo or video was taken, renames it to a standardized format, and sorts it into a nested directory structure by **Year** and **Month**.

## ✨ Key Features

- **Recursive Scanning:** Automatically crawls through nested subdirectories in your source folder.
- **Smart Date Extraction:** Follows a strict priority system to find the most accurate date:
  - **Priority 1: EXIF Metadata** (Date Taken from `DateTimeOriginal` or `DateTimeDigitized` for photos; creation date for videos).
  - **Priority 2: File Modification Date** (System `mtime`).
  - **Priority 3: File Creation Date** (System `ctime`).
- **HEIF/HEIC Support:** Includes full support for modern iPhone photo formats.
- **Smart Renaming:** Renames files to `YYYYMMDDHHMMSS_Seq.ext` for chronological sorting.
- **Organized Structure:** Automatically sorts files into `Year/Month/Day` subdirectories (e.g., `2025/10/sun, Oct 5, 2025/`).
- **Duplicate Prevention:** Checks for existing files in the destination before moving.
- **Duplicate Identification:** Includes a utility to find identical files across subdirectories, even if they have different names.
- **Bulk Metadata Updater:** Includes a utility to fix incorrect or missing metadata using local `date.txt` files.
- **Smart Video Date Correction:** Automatically detects and fixes the "66-year shift" (1948 -> 2014) common in older 3GP/MP4 files.

## 🛠️ Prerequisites

Ensure you have Python 3.8+ installed.

### Install Dependencies

```bash
pip install -r requirements.txt
```

*Dependencies include: `Pillow` (Images), `hachoir` (Video metadata), and `pillow-heif` (HEIF support).*

## 📖 Usage

Run the script from the command line by specifying the **source** directory (where your messy photos are) and the **target** directory (where you want them organized).

```bash
python organize_photos.py "C:\Users\Name\Pictures\OldCamera" "D:\OrganizedPhotos"
```

### Script Arguments:
- `source`: The directory to scan for media files.
- `target`: The base directory where organized files will be placed.

## 📂 Example Output

### Before:
```text
OldCamera/
├── IMG_001.JPG (Taken 2021-05-12)
├── random_folder/
│   └── VIDEO_01.MP4 (Taken 2022-01-05)
```

### After:
```text
OrganizedPhotos/
├── 2021/
│   └── 05/
│       └── wed, May 12, 2021/
│           └── 20210512143005_01.jpg
├── 2022/
│   └── 01/
│       └── wed, Jan 05, 2022/
│           └── 20220105091500_01.mp4
└── review/
    └── corrupted_image.jpg  (If metadata could not be read)
```

## 🛠️ Utilities

### `update_metadata.py` - Bulk Metadata Fixer
If you have folders of photos with incorrect or missing metadata, you can update them in bulk using this utility.

#### **Preparation:**
1.  **ExifTool:** Place `exiftool.exe` in the same folder as the script (`c:\mydoc\learn\PhotoOrg`).
2.  **`date.txt`:** In each folder you want to update, create a file named `date.txt` containing the desired timestamp (e.g., `2023:08:15 10:30:00`).

#### **Usage:**
```bash
# Update a specific folder and its subfolders
python update_metadata.py "C:\Path\To\Your\Photos"

# Update the folder you are currently in
python update_metadata.py
```

### `find_duplicates.py` - Content-Based Duplicate Finder & Cleaner
This script identifies identical files by comparing their **MD5 hash** (content), ignoring their filenames. It recursively scans all subdirectories and groups files by size to speed up the process.

#### **Key Features:**
- **Recursive Scan:** Searches through all subfolders within the target directory.
- **Content Matching:** Uses MD5 hashing to ensure files are 100% identical.
- **Smart Cleanup:** Identifies duplicates and allows you to keep the first version alphabetically while deleting the others.

#### **Usage:**
```bash
# 1. SCAN (Dry Run) - See what duplicates exist without deleting anything
python find_duplicates.py "C:\Path\To\Your\Photos"

# 2. DELETE - Actually remove the duplicates (keeps one 'original' per set)
python find_duplicates.py "C:\Path\To\Your\Photos" --delete

# 3. ADVANCED - Check ALL file types (not just photos/videos)
python find_duplicates.py "C:\Path\To\Files" --all --delete
```

### `fix_extensions.py` - Extension Fixer
A simple utility to recursively rename files with incorrect `.mp` extensions to the standard `.mp4` format.

#### **Usage:**
```bash
# Rename all .mp files to .mp4 in a specific folder
python fix_extensions.py "C:\Path\To\Your\Photos"

# Rename in the current folder
python fix_extensions.py
```

### `summarize_log.py`
Run this script to see a quick count of how many files of each type were processed based on the log file:
```bash
python summarize_log.py
```

## 📝 Logging
All operations are logged to `photo_organizer.log`. This file tracks every file moved, its original path, and any errors encountered during processing.

---
*Created with ❤️ to keep your memories organized.*
