import sys
import os

# Add saas_module to path
sys.path.insert(0, os.path.join(os.getcwd(), "saas_module"))

try:
    print("Trying modern import...")
    from moviepy import ImageClip, AudioFileClip, concatenate_videoclips, TextClip, CompositeVideoClip
    print("Modern import success!")
except Exception as e:
    print(f"Modern import failed: {e}")
    import traceback
    traceback.print_exc()

try:
    print("\nTrying old import...")
    from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips, TextClip, CompositeVideoClip
    print("Old import success!")
except Exception as e:
    print(f"Old import failed: {e}")
