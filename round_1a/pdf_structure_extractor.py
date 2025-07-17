#!/usr/bin/env python3
"""
PDF Structure Extractor for Adobe Hackathon Round 1A
Extracts title and hierarchical headings (H1, H2, H3) from PDF documents
"""

import json
import os
import sys
from pathlib import Path
import re
from typing import Dict, List, Any, Optional, Tuple
import logging

# Core libraries
import fitz  # PyMuPDF
import numpy as np
from collections import defaultdict, Counter

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PDFStructureExtractor:
    def __init__(self):
        self.font_size_threshold = 2.0  # Minimum difference for heading detection
        self.min_heading_size = 10.0    # Minimum font size for headings
        self.max_heading_length = 200   # Maximum character length for headings
        
    def extract_text_with_properties(self, doc: fitz.Document) -> List[Dict]:
        """Extract text with font properties from PDF"""
        text_elements = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            blocks = page.get_text("dict")
            
            for block in blocks["blocks"]:
                if "lines" in block:
                    for line in block["lines"]:
                        for span in line["spans"]:
                            text = span["text"].strip()
                            if text and len(text) > 1:
                                text_elements.append({
                                    "text": text,
                                    "page": page_num + 1,
                                    "font_size": span["size"],
                                    "font_flags": span["flags"],
                                    "font_name": span["font"],
                                    "bbox": span["bbox"]
                                })
        
        return text_elements
    
    def is_likely_heading(self, element: Dict, avg_font_size: float, common_font_size: float) -> bool:
        """Determine if a text element is likely a heading"""
        text = element["text"]
        font_size = element["font_size"]
        font_flags = element["font_flags"]
        
        # Skip if text is too long
        if len(text) > self.max_heading_length:
            return False
            
        # Skip if font size is too small
        if font_size < self.min_heading_size:
            return False
            
        # Check if font size is significantly larger than average
        size_threshold = max(avg_font_size + self.font_size_threshold, common_font_size + 1.0)
        if font_size >= size_threshold:
            return True
            
        # Check if text has bold formatting
        if font_flags & 2**4:  # Bold flag
            return True
            
        # Check heading patterns
        heading_patterns = [
            r'^\d+\.?\s+[A-Z]',  # Numbered headings
            r'^[A-Z][A-Z\s]+$',  # ALL CAPS
            r'^[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*$',  # Title Case
            r'^(Chapter|Section|Part)\s+\d+',  # Chapter/Section markers
            r'^\d+\.\d+\s+',  # Subsection numbers
        ]
        
        for pattern in heading_patterns:
            if re.match(pattern, text):
                return True
                
        return False
    
    def extract_title(self, text_elements: List[Dict]) -> str:
        """Extract document title"""
        # Look for title on first few pages
        first_page_elements = [e for e in text_elements if e["page"] <= 2]
        
        if not first_page_elements:
            return "Untitled Document"
            
        # Find element with largest font size on first page
        title_candidate = max(first_page_elements, key=lambda x: x["font_size"])
        
        # Additional title validation
        title_text = title_candidate["text"]
        
        # Clean up title
        title_text = re.sub(r'^\d+\.?\s*', '', title_text)  # Remove leading numbers
        title_text = title_text.strip()
        
        return title_text if title_text else "Untitled Document"
    
    def classify_heading_level(self, element: Dict, font_size_levels: List[float]) -> str:
        """Classify heading level based on font size"""
        font_size = element["font_size"]
        
        # Sort font sizes in descending order
        sorted_sizes = sorted(font_size_levels, reverse=True)
        
        if len(sorted_sizes) == 1:
            return "H1"
        elif len(sorted_sizes) == 2:
            return "H1" if font_size == sorted_sizes[0] else "H2"
        else:
            if font_size == sorted_sizes[0]:
                return "H1"
            elif font_size == sorted_sizes[1]:
                return "H2"
            else:
                return "H3"
    
    def extract_outline(self, pdf_path: str) -> Dict[str, Any]:
        """Extract structured outline from PDF"""
        try:
            doc = fitz.open(pdf_path)
            text_elements = self.extract_text_with_properties(doc)
            
            if not text_elements:
                return {"title": "Empty Document", "outline": []}
            
            # Calculate font statistics
            font_sizes = [e["font_size"] for e in text_elements]
            avg_font_size = np.mean(font_sizes)
            common_font_size = Counter(font_sizes).most_common(1)[0][0]
            
            # Extract title
            title = self.extract_title(text_elements)
            
            # Filter potential headings
            headings = []
            for element in text_elements:
                if self.is_likely_heading(element, avg_font_size, common_font_size):
                    headings.append(element)
            
            # Remove duplicates while preserving order
            unique_headings = []
            seen_texts = set()
            for heading in headings:
                if heading["text"] not in seen_texts:
                    unique_headings.append(heading)
                    seen_texts.add(heading["text"])
            
            # Get unique font sizes for level classification
            heading_font_sizes = list(set([h["font_size"] for h in unique_headings]))
            
            # Build outline
            outline = []
            for heading in unique_headings:
                level = self.classify_heading_level(heading, heading_font_sizes)
                outline.append({
                    "level": level,
                    "text": heading["text"],
                    "page": heading["page"]
                })
            
            doc.close()
            
            return {
                "title": title,
                "outline": outline
            }
            
        except Exception as e:
            logger.error(f"Error processing {pdf_path}: {str(e)}")
            return {"title": "Error Processing Document", "outline": []}

def process_pdfs(input_dir: str, output_dir: str):
    """Process all PDFs in input directory"""
    extractor = PDFStructureExtractor()
    
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    pdf_files = list(input_path.glob("*.pdf"))
    
    if not pdf_files:
        logger.warning("No PDF files found in input directory")
        return
    
    for pdf_file in pdf_files:
        logger.info(f"Processing {pdf_file.name}")
        
        try:
            result = extractor.extract_outline(str(pdf_file))
            
            # Save output
            output_file = output_path / f"{pdf_file.stem}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Generated {output_file.name}")
            
        except Exception as e:
            logger.error(f"Failed to process {pdf_file.name}: {str(e)}")

def main():
    """Main execution function"""
    input_dir = "/app/input"
    output_dir = "/app/output"
    
    # Ensure directories exist
    os.makedirs(output_dir, exist_ok=True)
    
    process_pdfs(input_dir, output_dir)

if __name__ == "__main__":
    main()
