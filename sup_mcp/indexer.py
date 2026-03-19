import os
import glob
from typing import List, Dict, Any
import pypdf
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup

REF_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../ref'))

def get_all_documents() -> List[str]:
    """Returns a list of all supported document paths in ref/"""
    extensions = ['*.pdf', '*.epub', '*.md', '*.txt']
    files = []
    for ext in extensions:
        files.extend(glob.glob(os.path.join(REF_DIR, ext)))
    return files

def extract_text_from_pdf(filepath: str) -> str:
    """Extracts text from a PDF file."""
    text = ""
    try:
        reader = pypdf.PdfReader(filepath)
        for page in reader.pages:
            text += page.extract_text() + "\n"
    except Exception as e:
        print(f"Error reading PDF {filepath}: {e}")
    return text

def extract_text_from_epub(filepath: str) -> str:
    """Extracts text from an EPUB file."""
    text = ""
    try:
        book = epub.read_epub(filepath)
        for item in book.get_items():
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                soup = BeautifulSoup(item.get_content(), 'html.parser')
                text += soup.get_text() + "\n"
    except Exception as e:
        print(f"Error reading EPUB {filepath}: {e}")
    return text

def get_document_content(filename: str) -> str:
    """Returns the content of a document by filename."""
    filepath = os.path.join(REF_DIR, filename)
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filename}")
    
    if filename.lower().endswith('.pdf'):
        return extract_text_from_pdf(filepath)
    elif filename.lower().endswith('.epub'):
        return extract_text_from_epub(filepath)
    elif filename.lower().endswith('.md') or filename.lower().endswith('.txt'):
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    else:
        return "Unsupported file format."

def list_documents() -> List[Dict[str, Any]]:
    """Returns metadata for all documents."""
    docs = []
    for filepath in get_all_documents():
        filename = os.path.basename(filepath)
        size = os.path.getsize(filepath)
        ext = os.path.splitext(filename)[1].lower().replace('.', '')
        docs.append({
            "filename": filename,
            "size": size,
            "type": ext
        })
    return docs
