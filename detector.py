import cv2
import pdfplumber
import easyocr
import re
import pandas as pd
import json
import os

# Ensure Unicode output in Windows
import sys
if sys.platform.startswith("win"):
    os.environ["PYTHONUTF8"] = "1"

# OCR Reader (English)
reader = easyocr.Reader(["en"], verbose=False)

# Regex pattern for dimensions (supports feet, inches, and scales)
DIMENSION_PATTERN = r"\b\d+'?\s*\d*\"?\s*[xX×]\s*\d+'?\s*\d*\"?\b"
SCALE_PATTERN = r"(\d+)\s*:\s*(\d+)"  # Matches scale formats like "1:50"


def extract_text_from_pdf(pdf_path):
    """Extracts text from a PDF file using pdfplumber."""
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text


def extract_text_from_image(image_path):
    """Extracts text from an image using EasyOCR."""
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError("Error loading image. Check the file path.")
    
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    extracted_text = reader.readtext(gray, detail=0)  # Extract text
    return " ".join(extracted_text)


def extract_dimensions(text):
    """Extracts dimensions (feet, inches) from text."""
    return re.findall(DIMENSION_PATTERN, text)


def extract_scale(text):
    """Extracts scale ratio from text (if mentioned)."""
    match = re.search(SCALE_PATTERN, text)
    if match:
        return int(match.group(1)), int(match.group(2))  # Return (scale, real-world)
    return None


def convert_to_feet(dimensions, scale=None):
    """Converts dimensions to feet, applying scale if necessary."""
    converted = []
    for dim in dimensions:
        parts = re.split(r"[xX×]", dim)
        if len(parts) == 2:
            width, height = parts[0].strip(), parts[1].strip()
            width_ft = parse_feet_inches(width)
            height_ft = parse_feet_inches(height)

            # Apply scale conversion
            if scale:
                width_ft *= scale
                height_ft *= scale

            converted.append((width_ft, height_ft))
    return converted


def parse_feet_inches(value):
    """Parses a dimension value in feet and inches (e.g., '12' or '5'8"') and converts it to feet."""
    match = re.match(r"(\d+)'?\s*(\d*)\"?", value)
    if match:
        feet = int(match.group(1))
        inches = int(match.group(2)) if match.group(2) else 0
        return feet + (inches / 12)
    return float(value)  # Handle pure numerical values


def save_to_csv(data, output_file="dimensions.csv"):
    """Saves extracted dimensions to a CSV file."""
    df = pd.DataFrame(data, columns=["Width (ft)", "Height (ft)"])
    df.to_csv(output_file, index=False)
    print(f"✅ Dimensions saved to {output_file}")


def save_to_json(data, output_file="dimensions.json"):
    """Saves extracted dimensions to a JSON file in the required format."""
    formatted_data = []
    for width, height in data:
        formatted_data.append({
            "length": f"{height} ft",
            "width": f"{width} ft",
            "unit": "feet"
        })
    
    with open(output_file, "w") as f:
        json.dump(formatted_data, f, indent=4)
    print(f"✅ Dimensions saved to {output_file}")



def process_file(file_path):
    """Determines file type (PDF or image) and extracts dimensions."""
    text = ""
    if file_path.lower().endswith(".pdf"):
        text = extract_text_from_pdf(file_path)
    else:
        text = extract_text_from_image(file_path)

    dimensions = extract_dimensions(text)
    scale = extract_scale(text)
    scale_factor = None
    if scale:
        scale_factor = scale[1] / scale[0]  # Convert scale (e.g., 1:50 → 50)

    converted_dimensions = convert_to_feet(dimensions, scale_factor)

    # Save to CSV and JSON
    save_to_csv(converted_dimensions)
    save_to_json(converted_dimensions)


# --- Run Extraction ---
file_path = "input.png"  # Change this to your file path
process_file(file_path)
