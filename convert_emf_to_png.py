"""
Convert all .emf files in the images directory to .png format.

Requirements:
- ImageMagick must be installed and in PATH
  Download from: https://imagemagick.org/script/download.php
  (Make sure to check "Add to PATH" during installation)

Usage:
  python convert_emf_to_png.py
"""

import os
import subprocess
from pathlib import Path

def convert_emf_to_png():
    images_dir = Path(__file__).parent / "images"
    
    if not images_dir.exists():
        print(f"Error: Images directory not found: {images_dir}")
        return
    
    emf_files = list(images_dir.glob("*.emf")) + list(images_dir.glob("*.EMF"))
    
    if not emf_files:
        print("No .emf files found in the images directory.")
        return
    
    print(f"Found {len(emf_files)} EMF files to convert...")
    
    success_count = 0
    error_count = 0
    
    for emf_file in emf_files:
        png_file = emf_file.with_suffix(".png")
        
        try:
            # Use ImageMagick's magick command
            result = subprocess.run(
                ["magick", "convert", str(emf_file), str(png_file)],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print(f"✓ Converted: {emf_file.name} -> {png_file.name}")
                success_count += 1
            else:
                print(f"✗ Error converting {emf_file.name}: {result.stderr}")
                error_count += 1
                
        except FileNotFoundError:
            print("Error: ImageMagick not found. Please install ImageMagick and add it to PATH.")
            print("Download from: https://imagemagick.org/script/download.php")
            return
        except Exception as e:
            print(f"✗ Error converting {emf_file.name}: {e}")
            error_count += 1
    
    print(f"\nConversion complete: {success_count} successful, {error_count} failed")

if __name__ == "__main__":
    convert_emf_to_png()
