from PIL import Image, ImageDraw, ImageFont
import io
import os
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Fallback font
DEFAULT_FONT_PATH = "arial.ttf" # Replace with actual path in production

def generate_preview(base_image_path: str, zones_config: dict, customizations: Dict[str, str]) -> bytes:
    """
    Generates a live preview by overlaying text onto a base template image.
    
    :param base_image_path: Path to the low-res web preview base image
    :param zones_config: From CardDesign.zones_json defining text bounds and styles
    :param customizations: User input, e.g. {"event_title": "Rahul & Priya"}
    :return: Bytes of the generated webp/jpeg image
    """
    try:
        # Load base image
        img = Image.open(base_image_path).convert("RGBA")
        draw = ImageDraw.Draw(img)
        
        # Iterate through defined zones
        for zone in zones_config.get("zones", []):
            zone_id = zone.get("id")
            if zone_id in customizations:
                text = customizations[zone_id]
                
                # Extract style properties
                x = zone["position"]["x"]
                y = zone["position"]["y"]
                font_size = zone["style"].get("fontSize", 24)
                color = zone["style"].get("color", "#000000")
                
                # In MVP, load a default font. 
                # Production: Map zone["style"]["fontFamily"] to a loaded .ttf/.otf file mapping
                try:
                    font = ImageFont.truetype(DEFAULT_FONT_PATH, font_size)
                except IOError:
                    font = ImageFont.load_default()
                
                # Draw text
                # We align text based on simple coordinates for mvp
                draw.text((x, y), text, fill=color, font=font)
        
        # Save to buffer
        buf = io.BytesIO()
        img.save(buf, format="WEBP", quality=80)
        return buf.getvalue()
        
    except Exception as e:
        logger.error(f"Failed to generate preview: {e}")
        raise ValueError("Could not generate image preview")
