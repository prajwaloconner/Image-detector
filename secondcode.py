import cv2
import pdfplumber
import easyocr
import re
import json
import os

# Ensure Unicode output in Windows
import sys
if sys.platform.startswith("win"):
    os.environ["PYTHONUTF8"] = "1"

# OCR Reader (English)
reader = easyocr.Reader(["en"], verbose=False)

# Regex patterns
DIMENSION_PATTERN = r"\b\d+'?\s*\d*\"?\s*[xX×]\s*\d+'?\s*\d*\"?\b"
SCALE_PATTERN = r"(\d+)\s*:\s*(\d+)"
ROOM_PATTERN = r"\b(Kitchen|Bedroom|Living Room|Hall|Bathroom|Balcony)\b"


def extract_text_from_pdf(pdf_path):
    """Extracts text from a PDF file."""
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
    extracted_text = reader.readtext(gray, detail=0)
    return " ".join(extracted_text)


def extract_dimensions(text):
    """Extracts dimensions from text."""
    return re.findall(DIMENSION_PATTERN, text)


def extract_rooms(text):
    """Extracts room labels from text."""
    return re.findall(ROOM_PATTERN, text)


def extract_scale(text):
    """Extracts scale ratio from text."""
    match = re.search(SCALE_PATTERN, text)
    if match:
        return int(match.group(1)), int(match.group(2))
    return None


def convert_to_feet(dimensions, scale=None):
    """Converts dimensions to feet, applying scale if necessary."""
    converted = []
    for dim in dimensions:
        parts = re.split(r"[xX×]", dim)
        if len(parts) == 2:
            width = parse_feet_inches(parts[0].strip())
            height = parse_feet_inches(parts[1].strip())
            if scale:
                width *= scale
                height *= scale
            converted.append((width, height))
    return converted


def parse_feet_inches(value):
    """Parses feet and inches values."""
    match = re.match(r"(\d+)'?\s*(\d*)\"?", value)
    if match:
        feet = int(match.group(1))
        inches = int(match.group(2)) if match.group(2) else 0
        return feet + (inches / 12)
    return float(value)


def save_to_json(data, output_file="dimensions.json"):
    """Saves extracted dimensions to a JSON file."""
    with open(output_file, "w") as f:
        json.dump(data, f, indent=4)
    print(f"✅ Dimensions saved to {output_file}")


def process_file(file_path):
    """Processes the input file and extracts labeled dimensions."""
    text = extract_text_from_pdf(file_path) if file_path.lower().endswith(".pdf") else extract_text_from_image(file_path)
    dimensions = extract_dimensions(text)
    rooms = extract_rooms(text)
    scale = extract_scale(text)
    scale_factor = scale[1] / scale[0] if scale else None
    converted_dimensions = convert_to_feet(dimensions, scale_factor)
    
    # Match dimensions to rooms (assuming sequential order)
    labeled_data = []
    for i, room in enumerate(rooms):
        if i < len(converted_dimensions):
            labeled_data.append({
                "name": room,
                "length": round(converted_dimensions[i][0], 2),
                "width": round(converted_dimensions[i][1], 2),
                "unit": "ft"
            })
    
    save_to_json({"rooms": labeled_data})


# --- Run Extraction ---
file_path = "input.png"  # Change to your file
process_file(file_path)