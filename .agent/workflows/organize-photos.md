---
description: Organize photos and videos by metadata timestamp
---

This script recursively scans a source directory, extracts metadata from photos (EXIF) and videos (QuickTime/MP4/etc.), and moves them to a target directory organized by year, month, and day (e.g., `2025/10/sun, Oct 5, 2025/`), renaming them to `YYYYMMDDHHMMSS_Seq.ext`.

### Prerequisite: Install dependencies
```bash
pip install -r requirements.txt
```

### Usage
Run the script by specifying the source and target directories:

```bash
python organize_photos.py "C:\Path\To\Source" "C:\Path\To\Target"
```

### Parameters
- `source`: The directory containing your unorganized photos and videos.
- `target`: The directory where the organized files will be placed (folders for each year will be created here).

### Logs
All operations and errors are logged to `photo_organizer.log`.
