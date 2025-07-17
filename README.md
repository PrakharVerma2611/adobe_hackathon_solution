# Adobe Hackathon – Connecting the Dots Challenge

A scalable, intelligent PDF processing solution for automated document structure extraction and persona-driven document analysis.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Project Structure](#project-structure)
- [How It Works](#how-it-works)
  - [Round 1A: Structure Extraction](#round-1a-structure-extraction)
  - [Round 1B: Persona-Driven Intelligence](#round-1b-persona-driven-intelligence)
- [Build & Run Instructions](#build--run-instructions)
- [Input & Output Formats](#input--output-formats)
- [Performance Optimizations](#performance-optimizations)
- [Technical Requirements](#technical-requirements)
- [Troubleshooting](#troubleshooting)
- [Future Enhancements](#future-enhancements)
- [License](#license)
- [Contact](#contact)

## Overview

This repository demonstrates a robust, multi-layered approach for:

- Extracting structured outlines from PDF files (Round 1A)
- Delivering persona-tailored document intelligence (Round 1B)

The system is **CPU-only**, containerized, and optimized for both speed and scalability, meeting all requirements of the Adobe Hackathon "Connecting the Dots" challenge.

## Features

- **Intelligent Heading Detection**: Font size, formatting, and pattern-based outline extraction
- **Persona-Driven Section Ranking**: Multi-factor relevance scoring considering persona, job, content length, and heading presence
- **Subsection Deep-Dive**: Granular extraction and ranking within relevant document sections
- **Scalable & Efficient**: Handles PDF batches with swift, sequential resource-constrained processing
- **Extensible**: Easily adaptable for new document types, personas, or task requirements
- **Error-Tolerant**: Graceful handling of corrupted, complex, or malformed PDFs

## Project Structure

```
.
├── Round1A/
│   ├── extract_structure.py
│   ├── Dockerfile
│   ├── requirements.txt
│   └── README.md
├── Round1B/
│   ├── persona_intelligence.py
│   ├── Dockerfile
│   ├── requirements.txt
│   └── approach_explanation.md
└── README.md
```

## How It Works

### Round 1A: Structure Extraction

- Extracts document outline using font analysis, formatting cues, and pattern recognition.
- Outputs titles, headings, and their hierarchy with page references.
- Features robust de-duplication, multi-language support, and handles complex layouts.

**Technologies:**  
PyMuPDF (fitz), NumPy, collections, regex

### Round 1B: Persona-Driven Intelligence

- Analyzes sections for relevance to a given persona and a "job-to-be-done".
- Uses keyword/TF-IDF similarity, content length, and heading weight for scoring.
- Produces refined summaries of top sections and granular content analysis.

**Technologies:**  
PyMuPDF (fitz), NumPy, scikit-learn, collections

## Build & Run Instructions

### Round 1A

```bash
# Build Docker image
docker build --platform linux/amd64 -t pdf-extractor:v1 .

# Run container
docker run --rm -v $(pwd)/input:/app/input -v $(pwd)/output:/app/output --network none pdf-extractor:v1
```

### Round 1B

```bash
# Build Docker image
docker build --platform linux/amd64 -t persona-intelligence:v1 .

# Run container
docker run --rm -v $(pwd)/input:/app/input -v $(pwd)/output:/app/output --network none persona-intelligence:v1
```

> Ensure input PDFs are placed in `/input` directory. Output will be available in `/output`.

## Input & Output Formats

### Input

- PDFs: `/input` directory (up to 50 pages each for Round 1A; 3-10 documents for Round 1B)
- For Round 1B:  
  - `persona.txt`: Persona description  
  - `job.txt`: Job-to-be-done description

### Output

#### Round 1A Example

```json
{
  "title": "Document Title",
  "outline": [
    {
      "level": "H1",
      "text": "Introduction",
      "page": 1
    },
    {
      "level": "H2",
      "text": "Background",
      "page": 2
    }
  ]
}
```

#### Round 1B Example

```json
{
  "metadata": {
    "input_documents": ["doc1.pdf", "doc2.pdf"],
    "persona": "PhD Researcher in Computational Biology",
    "job_to_be_done": "Literature review on GNN methods",
    "processing_timestamp": "2025-01-15T10:30:00"
  },
  "extracted_sections": [
    {
      "document": "paper1.pdf",
      "page_number": 3,
      "section_title": "Methodology",
      "importance_rank": 1
    }
  ],
  "subsection_analysis": [
    {
      "document": "paper1.pdf",
      "page_number": 3,
      "refined_text": "The proposed method uses graph neural networks...",
      "relevance_score": 0.85
    }
  ]
}
```

## Performance Optimizations

- **Single-Pass Text Extraction**
- **Vectorized Font Analysis (NumPy)**
- **Pattern/Regex Caching**
- **Efficient Chunked Document Processing**
- **Selective Subsection Analysis**
- **CPU and Memory Efficient** – Handles 50-page PDFs in ≤ 10s and multi-doc sets in ≤ 60s (on typical hardware)

## Technical Requirements

- **Python:** 3.9
- **Docker** (Linux/AMD64)
- **Memory:** 16GB RAM recommended
- **CPU-only** (no GPU required)
- **No external network access required**

## Troubleshooting

- **Docker Build Fails:**  
  - Ensure you're specifying the correct architecture (`--platform linux/amd64`)
  - Check internet connection for dependency installation

- **PDF Processing Errors:**  
  - Verify PDF integrity and input/output directory permissions

- **Memory Issues:**  
  - Reduce batch size, confirm sufficient system memory

- **Enable Debug Mode:**  
  - Set environment variable `DEBUG=1` during container run

## Future Enhancements

- OCR Integration for scanned and image-heavy PDFs
- Enhanced layout and multi-column analysis
- Automatic language detection
- Semantic similarity scoring with advanced embeddings
- Entity recognition and citation analysis
- Visual, table, and multi-modal content support

## License

- **PyMuPDF:** Apache 2.0  
- **NumPy & Scikit-learn:** BSD  
- See individual library documentation for more details.

## Contact

For questions or support, please refer to the project documentation or reach out to the development team.
