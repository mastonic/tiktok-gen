import os
from pathlib import Path

posts_dir = Path(r"c:\Users\w110480\OneDrive - Worldline\Documents\perso\tiktok-gen\backend\blog\posts")

if posts_dir.exists():
    for md_file in posts_dir.glob("*.md"):
        content = md_file.read_text(encoding="utf-8")
        if "http://localhost:5656" in content:
            new_content = content.replace("http://localhost:5656", "")
            md_file.write_text(new_content, encoding="utf-8")
            print(f"Fixed {md_file.name}")
