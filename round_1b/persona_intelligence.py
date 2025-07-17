#!/usr/bin/env python3
"""
Persona-Driven Document Intelligence for Adobe Hackathon Round 1B
Extracts and ranks relevant sections based on persona and job-to-be-done
"""

import json
import os
import sys
from pathlib import Path
import re
from typing import Dict, List, Any, Optional, Tuple
import logging
from datetime import datetime
import math

# Core libraries
import fitz  # PyMuPDF
import numpy as np
from collections import defaultdict, Counter
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DocumentIntelligence:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 2),
            lowercase=True
        )
        
    def extract_sections(self, doc: fitz.Document, doc_name: str) -> List[Dict]:
        """Extract sections from PDF with content"""
        sections = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            blocks = page.get_text("dict")
            
            current_section = {
                "document": doc_name,
                "page": page_num + 1,
                "section_title": f"Page {page_num + 1}",
                "content": "",
                "font_sizes": [],
                "is_heading": False
            }
            
            for block in blocks["blocks"]:
                if "lines" in block:
                    block_text = ""
                    block_font_sizes = []
                    
                    for line in block["lines"]:
                        line_text = ""
                        for span in line["spans"]:
                            text = span["text"].strip()
                            if text:
                                line_text += text + " "
                                block_font_sizes.append(span["size"])
                        
                        if line_text.strip():
                            block_text += line_text + "\n"
                    
                    if block_text.strip():
                        # Check if this might be a section heading
                        if self.is_potential_heading(block_text, block_font_sizes):
                            # Save previous section if it has content
                            if current_section["content"].strip():
                                sections.append(current_section.copy())
                            
                            # Start new section
                            current_section = {
                                "document": doc_name,
                                "page": page_num + 1,
                                "section_title": block_text.strip()[:100],
                                "content": block_text,
                                "font_sizes": block_font_sizes,
                                "is_heading": True
                            }
                        else:
                            current_section["content"] += block_text
                            current_section["font_sizes"].extend(block_font_sizes)
            
            # Add final section for the page
            if current_section["content"].strip():
                sections.append(current_section)
        
        return sections
    
    def is_potential_heading(self, text: str, font_sizes: List[float]) -> bool:
        """Check if text block is likely a heading"""
        if not text or len(text.strip()) > 200:
            return False
            
        # Check font size (if larger than average)
        if font_sizes:
            avg_size = np.mean(font_sizes)
            if avg_size > 12:  # Threshold for heading font size
                return True
        
        # Check heading patterns
        heading_patterns = [
            r'^\d+\.?\s+[A-Z]',  # Numbered headings
            r'^[A-Z][A-Z\s]+$',  # ALL CAPS
            r'^[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*:?\s*$',  # Title Case
            r'^(Chapter|Section|Part|Abstract|Introduction|Conclusion|References)\s*:?\s*$',
            r'^\d+\.\d+\s+',  # Subsection numbers
        ]
        
        for pattern in heading_patterns:
            if re.match(pattern, text.strip(), re.IGNORECASE):
                return True
                
        return False
    
    def calculate_relevance_score(self, section: Dict, persona: str, job: str) -> float:
        """Calculate relevance score for a section"""
        content = section["content"].lower()
        section_title = section["section_title"].lower()
        
        # Create combined query from persona and job
        query = f"{persona} {job}".lower()
        
        # Keyword matching score
        persona_keywords = self.extract_keywords(persona)
        job_keywords = self.extract_keywords(job)
        
        persona_score = sum(1 for keyword in persona_keywords if keyword in content or keyword in section_title)
        job_score = sum(1 for keyword in job_keywords if keyword in content or keyword in section_title)
        
        # Length penalty (prefer substantial sections)
        length_score = min(len(content) / 1000, 1.0)
        
        # Heading bonus
        heading_bonus = 0.2 if section.get("is_heading", False) else 0
        
        # Combine scores
        total_score = (persona_score * 0.3 + job_score * 0.4 + length_score * 0.2 + heading_bonus)
        
        return total_score
    
    def extract_keywords(self, text: str) -> List[str]:
        """Extract important keywords from text"""
        # Simple keyword extraction
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        
        # Remove common words
        stopwords = {'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had', 'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his', 'how', 'man', 'new', 'now', 'old', 'see', 'two', 'who', 'boy', 'did', 'its', 'let', 'put', 'say', 'she', 'too', 'use'}
        
        keywords = [word for word in words if word not in stopwords and len(word) > 3]
        
        return list(set(keywords))
    
    def extract_subsections(self, section: Dict, persona: str, job: str) -> List[Dict]:
        """Extract and rank subsections from a section"""
        content = section["content"]
        
        # Split content into paragraphs
        paragraphs = [p.strip() for p in content.split('\n') if p.strip() and len(p.strip()) > 50]
        
        subsections = []
        for i, paragraph in enumerate(paragraphs[:5]):  # Limit to top 5 paragraphs
            # Refine text (clean up)
            refined_text = self.refine_text(paragraph)
            
            if refined_text and len(refined_text) > 30:
                subsection = {
                    "document": section["document"],
                    "page_number": section["page"],
                    "refined_text": refined_text,
                    "relevance_score": self.calculate_text_relevance(refined_text, persona, job)
                }
                subsections.append(subsection)
        
        # Sort by relevance score
        subsections.sort(key=lambda x: x["relevance_score"], reverse=True)
        
        return subsections[:3]  # Return top 3 subsections
    
    def refine_text(self, text: str) -> str:
        """Clean and refine text"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s.,!?;:()\-]', '', text)
        
        # Capitalize first letter
        text = text.strip()
        if text:
            text = text[0].upper() + text[1:] if len(text) > 1 else text.upper()
        
        return text
    
    def calculate_text_relevance(self, text: str, persona: str, job: str) -> float:
        """Calculate relevance score for text fragment"""
        text_lower = text.lower()
        
        # Keyword matching
        persona_keywords = self.extract_keywords(persona)
        job_keywords = self.extract_keywords(job)
        
        persona_matches = sum(1 for keyword in persona_keywords if keyword in text_lower)
        job_matches = sum(1 for keyword in job_keywords if keyword in text_lower)
        
        # Normalize by text length
        text_length = len(text.split())
        if text_length > 0:
            score = (persona_matches * 0.4 + job_matches * 0.6) / math.sqrt(text_length)
        else:
            score = 0
        
        return score
    
    def process_documents(self, input_dir: str, persona: str, job: str) -> Dict[str, Any]:
        """Process all documents and extract relevant sections"""
        input_path = Path(input_dir)
        pdf_files = list(input_path.glob("*.pdf"))
        
        if not pdf_files:
            logger.warning("No PDF files found in input directory")
            return self.create_empty_result(persona, job)
        
        all_sections = []
        document_names = []
        
        # Process each PDF
        for pdf_file in pdf_files:
            logger.info(f"Processing {pdf_file.name}")
            
            try:
                doc = fitz.open(str(pdf_file))
                sections = self.extract_sections(doc, pdf_file.name)
                all_sections.extend(sections)
                document_names.append(pdf_file.name)
                doc.close()
                
            except Exception as e:
                logger.error(f"Error processing {pdf_file.name}: {str(e)}")
        
        # Calculate relevance scores for all sections
        for section in all_sections:
            section["relevance_score"] = self.calculate_relevance_score(section, persona, job)
        
        # Sort sections by relevance
        all_sections.sort(key=lambda x: x["relevance_score"], reverse=True)
        
        # Select top sections
        top_sections = all_sections[:10]  # Top 10 sections
        
        # Build extracted sections output
        extracted_sections = []
        for i, section in enumerate(top_sections):
            extracted_sections.append({
                "document": section["document"],
                "page_number": section["page"],
                "section_title": section["section_title"],
                "importance_rank": i + 1
            })
        
        # Build subsection analysis
        subsection_analysis = []
        for section in top_sections[:5]:  # Top 5 sections for subsection analysis
            subsections = self.extract_subsections(section, persona, job)
            subsection_analysis.extend(subsections)
        
        # Sort subsections by relevance
        subsection_analysis.sort(key=lambda x: x["relevance_score"], reverse=True)
        
        # Build final result
        result = {
            "metadata": {
                "input_documents": document_names,
                "persona": persona,
                "job_to_be_done": job,
                "processing_timestamp": datetime.now().isoformat()
            },
            "extracted_sections": extracted_sections,
            "subsection_analysis": subsection_analysis[:10]  # Top 10 subsections
        }
        
        return result
    
    def create_empty_result(self, persona: str, job: str) -> Dict[str, Any]:
        """Create empty result structure"""
        return {
            "metadata": {
                "input_documents": [],
                "persona": persona,
                "job_to_be_done": job,
                "processing_timestamp": datetime.now().isoformat()
            },
            "extracted_sections": [],
            "subsection_analysis": []
        }

def main():
    """Main execution function"""
    input_dir = "/app/input"
    output_dir = "/app/output"
    
    # Ensure directories exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Read persona and job from input files (expected format)
    persona_file = Path(input_dir) / "persona.txt"
    job_file = Path(input_dir) / "job.txt"
    
    try:
        if persona_file.exists():
            with open(persona_file, 'r', encoding='utf-8') as f:
                persona = f.read().strip()
        else:
            persona = "General Researcher"
            
        if job_file.exists():
            with open(job_file, 'r', encoding='utf-8') as f:
                job = f.read().strip()
        else:
            job = "Extract key information from documents"
            
    except Exception as e:
        logger.error(f"Error reading persona/job files: {str(e)}")
        persona = "General Researcher"
        job = "Extract key information from documents"
    
    # Process documents
    intelligence = DocumentIntelligence()
    result = intelligence.process_documents(input_dir, persona, job)
    
    # Save output
    output_file = Path(output_dir) / "challenge1b_output.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Generated {output_file.name}")

if __name__ == "__main__":
    main()
