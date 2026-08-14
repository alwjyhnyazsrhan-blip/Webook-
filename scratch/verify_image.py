from PIL import Image
import os
import sys

def verify_image(path):
    if not os.path.exists(path):
        print(f"ERROR: File not found at {path}")
        return
    
    try:
        img = Image.open(path)
        width, height = img.size
        print(f"PATH: {path}")
        print(f"DIMENSIONS: {width}x{height}")
        print(f"MODE: {img.mode}")
        print(f"SIZE: {os.path.getsize(path)} bytes")
        
        # Check for non-blank
        extrema = img.convert("L").getextrema()
        print(f"EXTREMA: {extrema}") # (min, max)
        if extrema[0] == extrema[1]:
            print("STATUS: BLANK")
        else:
            print("STATUS: VALID_CONTENT")
            
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    path = r'C:\tmp\webook_seatmaps\spl-week-34-al-hazem-vs-al-taawoun-3710-rsl-25-26-al-hazem-vs-al-taawoun-1776776594.png'
    verify_image(path)
