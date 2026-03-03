
import re
from collections import Counter
import os

log_file_path = r'c:\mydoc\learn\PhotoOrg\photo_organizer.log'

extension_counter = Counter()

# Regex to match the extension at the end of the source file path
# Example: Moving: E:\...\20190108_153005.jpg ->
moving_pattern = re.compile(r'Moving:.*?\.(?P<ext>[a-zA-Z0-9]+)\s+->')

if os.path.exists(log_file_path):
    with open(log_file_path, 'r', encoding='utf-8') as f:
        for line in f:
            match = moving_pattern.search(line)
            if match:
                ext = match.group('ext').lower()
                extension_counter[ext] += 1

    print("File Extension Summary:")
    for ext, count in sorted(extension_counter.items(), key=lambda x: x[1], reverse=True):
        print(f"{ext} {count}")
else:
    print(f"Log file not found at {log_file_path}")
