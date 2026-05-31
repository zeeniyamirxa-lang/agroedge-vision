import os
import io
import json
import torch
import torch.nn as nn
from torchvision import transforms, models
from PIL import Image
import numpy as np

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────
MODEL_PATH = "leaf_model.pth"
CLASS_NAMES_PATH = "class_names.json"

# ── Google Drive model ID (paste your file ID here after uploading) ──────────
# Get this from your Google Drive share link:
# https://drive.google.com/file/d/YOUR_FILE_ID_HERE/view
GDRIVE_FILE_ID = "1CWKB9tEHeInSPyeCdwos75Msj4eVDbi7"

# Global model and class mapping references (lazy loaded)
_model = None
_class_names = None

# ─────────────────────────────────────────────────────────────────────────────
# MODEL ARCHITECTURE DEFINITION (Must match train.py exactly)
# ─────────────────────────────────────────────────────────────────────────────
class CustomLeafClassifier(nn.Module):
    """
    Custom transfer learning neural network using ResNet-50 backbone.
    """
    def __init__(self, num_classes):
        super(CustomLeafClassifier, self).__init__()
        # Load backbone (without weights; load_state_dict will load trained weights)
        self.backbone = models.resnet50()
        in_features = self.backbone.fc.in_features
        self.backbone.fc = nn.Identity()
        
        # Custom head
        self.classifier = nn.Sequential(
            nn.Linear(in_features, 512),
            nn.BatchNorm1d(512),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(512, num_classes)
        )
        
    def forward(self, x):
        features = self.backbone(x)
        logits = self.classifier(features)
        return logits


# ─────────────────────────────────────────────────────────────────────────────
# HELPER LOADER FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────
def _download_model_if_needed():
    """
    Downloads leaf_model.pth from Google Drive if it is not present locally.
    This runs automatically on Streamlit Cloud where the file cannot be stored in GitHub.
    """
    if os.path.exists(MODEL_PATH):
        return  # Already present — nothing to do

    if GDRIVE_FILE_ID == "YOUR_FILE_ID_HERE":
        print("[-] Google Drive file ID not configured. Skipping download.")
        return

    try:
        import gdown
        print("[*] Model not found locally. Downloading from Google Drive...")
        url = f"https://drive.google.com/uc?id={GDRIVE_FILE_ID}"
        gdown.download(url, MODEL_PATH, quiet=False)
        print("[+] Model downloaded successfully!")
    except Exception as e:
        print(f"[-] Failed to download model: {e}")


def load_custom_model():
    """
    Loads model weights and class labels if they exist.
    Auto-downloads from Google Drive on first run if needed.
    """
    global _model, _class_names
    
    # If already loaded, return cached versions
    if _model is not None:
        return _model, _class_names

    # Try to download model from Google Drive if not present
    _download_model_if_needed()
        
    # Check if files exist
    if not os.path.exists(MODEL_PATH) or not os.path.exists(CLASS_NAMES_PATH):
        print(f"[-] Warning: Custom model weights ({MODEL_PATH}) or class labels ({CLASS_NAMES_PATH}) not found.")
        print("[*] Running app in Mock Demonstration Mode.")
        return None, None
        
    try:
        # Load class names
        with open(CLASS_NAMES_PATH, "r") as f:
            _class_names = json.load(f)
            
        # Initialize model architecture matching the label count
        num_classes = len(_class_names)
        _model = CustomLeafClassifier(num_classes=num_classes)
        
        # Load weights onto CPU (safe for all machines)
        state_dict = torch.load(MODEL_PATH, map_location=torch.device("cpu"))
        _model.load_state_dict(state_dict)
        _model.eval()
        
        print("[+] Custom model weights and class list successfully loaded!")
        return _model, _class_names
    except Exception as e:
        print(f"[-] Error loading custom model: {e}")
        return None, None


def is_leaf_image(pil_image, min_leaf_fraction: float = 0.03) -> bool:
    """
    Pre-screens an image to check if it likely contains a leaf.
    Returns False if fewer than `min_leaf_fraction` of pixels look like
    leaf material (green or yellow/brown), indicating a non-plant photo.
    """
    img_np = np.array(pil_image.resize((224, 224)))
    r = img_np[:, :, 0].astype(float)
    g = img_np[:, :, 1].astype(float)
    b = img_np[:, :, 2].astype(float)

    is_green        = (g > r) & (g > b) & (g > 40)
    is_yellow_brown = (r > b) & (g > b) & (np.abs(r.astype(float) - g) < 70) & (r > 40)
    leaf_pixels     = np.sum(is_green | is_yellow_brown)
    total_pixels    = img_np.shape[0] * img_np.shape[1]

    return (leaf_pixels / total_pixels) >= min_leaf_fraction


def clean_and_crop_leaf(pil_image):
    """
    Locates the leaf in the image by color segmentation, crops the image 
    to the leaf's bounding box, and replaces the background with a neutral 
    gray color to match the PlantVillage training set layout.
    """
    img_np = np.array(pil_image)
    h_orig, w_orig, _ = img_np.shape
    
    r = img_np[:, :, 0].astype(float)
    g = img_np[:, :, 1].astype(float)
    b = img_np[:, :, 2].astype(float)
    
    # 1. Segment leaf color ranges (Green or Yellow/Brown)
    is_green = (g > r) & (g > b) & (g > 30)
    is_yellow_brown = (r > b) & (g > b) & (np.abs(r - g) < 60) & (r > 30)
    is_leaf = is_green | is_yellow_brown
    
    # 2. Crop to leaf bounding box
    y_indices, x_indices = np.where(is_leaf)
    if len(y_indices) > 0 and len(x_indices) > 0:
        y_min, y_max = y_indices.min(), y_indices.max()
        x_min, x_max = x_indices.min(), x_indices.max()
        
        # Add padding (15 pixels)
        pad = 15
        y_min = max(0, y_min - pad)
        y_max = min(h_orig - 1, y_max + pad)
        x_min = max(0, x_min - pad)
        x_max = min(w_orig - 1, x_max + pad)
        
        cropped_img = img_np[y_min:y_max+1, x_min:x_max+1]
        cropped_mask = is_leaf[y_min:y_max+1, x_min:x_max+1]
        
        # Create a neutral gray background (matching PlantVillage)
        cleaned_np = np.ones_like(cropped_img) * 128
        cleaned_np[cropped_mask] = cropped_img[cropped_mask]
        
        return Image.fromarray(cleaned_np.astype(np.uint8))
        
    return pil_image

def format_disease_name(raw_name: str) -> str:
    """
    Formats the raw dataset folder name into a beautiful, human-readable label.
    Example: "Tomato___Tomato_Yellow_Leaf_Curl_Virus" -> "Tomato - Yellow Leaf Curl Virus"
    Example: "Apple___healthy" -> "Healthy Apple"
    """
    # Replace triple underscores with a split
    if "___" in raw_name:
        parts = raw_name.split("___")
        plant = parts[0].strip()
        condition = parts[1].strip()
    elif "__" in raw_name:
        parts = raw_name.split("__")
        plant = parts[0].strip()
        condition = parts[1].strip()
    else:
        plant = raw_name
        condition = ""
            
    # Clean up plant name (remove underscores, brackets)
    plant = plant.replace("_", " ").replace("(including sour)", "").replace("  ", " ").strip().title()
    if "Pepper, Bell" in plant or "Pepper" in plant:
        plant = "Bell Pepper"
    elif "Corn" in plant:
        plant = "Corn"
        
    # Clean up condition
    condition = condition.replace("_", " ").replace("  ", " ").strip()
    
    # Handle healthy cases
    if condition.lower() == "healthy" or not condition:
        return f"Healthy {plant}"
        
    # Remove redundant plant name prefix from the condition if present
    # E.g. Tomato (Tomato Yellow Leaf Curl Virus) -> Tomato (Yellow Leaf Curl Virus)
    clean_plant_lower = plant.lower().replace("bell pepper", "pepper").replace("corn", "corn")
    if condition.lower().startswith(clean_plant_lower):
        condition = condition[len(clean_plant_lower):].strip()
        
    condition = condition.strip().title()
    return f"{plant} ({condition})"

def get_plant_species(raw_name: str) -> str:
    """
    Extracts the main plant species name from the raw class folder name.
    """
    if "___" in raw_name:
        plant = raw_name.split("___")[0].strip()
    elif "__" in raw_name:
        plant = raw_name.split("__")[0].strip()
    else:
        plant = raw_name
    
    plant_lower = plant.lower()
    if "tomato" in plant_lower:
        return "tomato"
    if "potato" in plant_lower:
        return "potato"
    if "apple" in plant_lower:
        return "apple"
    if "corn" in plant_lower:
        return "corn"
    if "grape" in plant_lower:
        return "grape"
    if "pepper" in plant_lower:
        return "pepper"
    if "strawberry" in plant_lower:
        return "strawberry"
    if "cherry" in plant_lower:
        return "cherry"
    if "peach" in plant_lower:
        return "peach"
    return plant_lower

# ─────────────────────────────────────────────────────────────────────────────
# INFERENCE PIPELINE
# ─────────────────────────────────────────────────────────────────────────────
def analyze_leaf_image(image_file) -> dict:
    """
    Analyzes an uploaded leaf image using the locally trained Custom PyTorch Model.
    If the model weights are not trained/saved yet, falls back to a mock mode
    to prevent application crashes and allow UI testing.
    """
    if image_file is None:
        raise ValueError("No image file provided for analysis.")

    # Read the raw bytes from the uploaded file
    image_bytes = image_file.getvalue()
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    
    # ── PRE-SCREEN: reject non-leaf images before running the model ──────────
    if not is_leaf_image(image):
        return {
            "disease_name": "No Leaf Detected",
            "confidence": 0.0,
            "top_predictions": [
                {"label": "No Leaf Detected", "confidence": 0.0}
            ],
            "cropped_image": image.resize((224, 224)),
            "no_leaf": True,
        }

    # Try to load custom model
    model, class_names = load_custom_model()

    # 1. Resize and crop the PIL image directly to get the AI Focus Area
    image_resized = image.resize((256, 256))
    left = (256 - 224) / 2
    top = (256 - 224) / 2
    right = (256 + 224) / 2
    bottom = (256 + 224) / 2
    image_cropped = image_resized.crop((left, top, right, bottom))
    
    # ── MOCK FALLBACK MODE (If model is not yet trained) ─────────────────────
    if model is None or class_names is None:
        filename = getattr(image_file, "name", "").lower()
        if "healthy" in filename:
            disease_name = "Healthy Tomato"
        elif "tomato" in filename:
            disease_name = "Tomato (Leaf Mold)"
        elif "apple" in filename:
            disease_name = "Apple (Scab)"
        else:
            disease_name = "Unknown Plant Disease"
            
        return {
            "disease_name": disease_name,
            "confidence": 0.85,
            "top_predictions": [
                {"label": disease_name, "confidence": 0.85},
                {"label": "Potato (Early Blight)", "confidence": 0.10},
                {"label": "Healthy Pepper", "confidence": 0.05}
            ],
            "cropped_image": image_cropped
        }
        
    # Preprocessing tensor transformation
    preprocess_tensor = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    
    # 2. Test-Time Augmentation (TTA) applied directly on the cropped leaf
    t1 = preprocess_tensor(image_cropped)
    t2 = preprocess_tensor(transforms.functional.hflip(image_cropped))
    t3 = preprocess_tensor(transforms.functional.vflip(image_cropped))
    t4 = preprocess_tensor(transforms.functional.rotate(image_cropped, 90))
    t5 = preprocess_tensor(transforms.functional.rotate(image_cropped, 270))
    
    input_batch = torch.stack([t1, t2, t3, t4, t5])
    
    # 3. Perform inference
    with torch.no_grad():
        logits = model(input_batch)
        probabilities = torch.softmax(logits, dim=1)
        mean_probabilities = torch.mean(probabilities, dim=0) # Average of all 5 runs
        
        # Get top 5 classes and confidence scores
        top_probs, top_indices = torch.topk(mean_probabilities, 5)
        
        # Format the top predictions for display (sorted by neural network confidence)
        top_predictions = []
        for i in range(5):
            p = float(top_probs[i].item())
            idx = str(top_indices[i].item())
            raw_name = class_names.get(idx, "Unknown Disease")
            top_predictions.append({
                "label": format_disease_name(raw_name),
                "confidence": p
            })
            
    top_conf = top_predictions[0]["confidence"]

    # ── CONFIDENCE FLOOR: if model has no strong opinion, image isn't a leaf ──
    if top_conf < 0.12:
        return {
            "disease_name": "No Leaf Detected",
            "confidence": 0.0,
            "top_predictions": [
                {"label": "No Leaf Detected", "confidence": 0.0}
            ],
            "cropped_image": image_cropped,
            "no_leaf": True,
        }

    return {
        "disease_name": top_predictions[0]["label"],
        "confidence": top_predictions[0]["confidence"],
        "top_predictions": top_predictions[:3],
        "cropped_image": image_cropped,
        "no_leaf": False,
    }
