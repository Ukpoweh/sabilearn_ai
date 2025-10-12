import os
import shutil

# --- Define base paths ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
output_dir = os.path.join(BASE_DIR, "data", "raw")
output_path = os.path.join(output_dir, "curriculum_pdfs")

os.makedirs(output_path, exist_ok=True)

# Local source folder (where all subfolders like JSS1, Pry4 exist)
LOCAL_NERDC_FOLDER = r"C:\Users\GRACEY\nerdc_pdfs"

# --- Validate source ---
if not os.path.exists(LOCAL_NERDC_FOLDER):
    raise FileNotFoundError(
        f"Source folder not found: {LOCAL_NERDC_FOLDER}. Please check the path."
    )

# --- Walk through subfolders recursively ---
copied_count = 0
for root, dirs, files in os.walk(LOCAL_NERDC_FOLDER):
    # preserve relative path inside destination
    rel_path = os.path.relpath(root, LOCAL_NERDC_FOLDER)
    dest_dir = os.path.join(output_path, rel_path)
    os.makedirs(dest_dir, exist_ok=True)

    for f in files:
        if f.lower().endswith(".pdf"):
            src = os.path.join(root, f)
            dest = os.path.join(dest_dir, f)
            shutil.copy2(src, dest)
            copied_count += 1
            print(f" Copied: {os.path.join(rel_path, f)}")

# --- Summary ---
if copied_count == 0:
    print(" No PDF files found in any subfolders.")
else:
    print(f"\n {copied_count} PDFs successfully copied to: {output_path}")
