import PyInstaller.__main__
import os

# Configuration to create
args = [
    'ui.py',                        # Main script
    '--name=LocalAI_Studio',        # .exe name
    '--windowed',                   # GUI mode
    '--onefile',                    # Package in a single file
    '--clean',                      # Clean cache from previous build
    '--noconfirm',                  # Does not ask for confirmation to rewrite
    
    # Complex dependencies
    '--collect-all=sentence_transformers',
    '--collect-all=torch',
    '--collect-all=faiss',
    '--collect-all=pypdf',
    
    # Icon or images:
    # '--add-data=pdf.png;.', 
    # '--icon=app_icon.ico',
]

print("🔨 Starting .exe build. This could take a few minutes...")

PyInstaller.__main__.run(args)

print("✅ Build completed. Open file in 'dist' folder.")