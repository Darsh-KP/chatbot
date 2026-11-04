# Script for ingesting data

import logging
from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

# ----------------------------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------------------------

data_folder_path = Path(__file__).resolve().parents[1] / "data"

chunk_size = 1000
chunk_overlap = 200

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------------------------
# PDF Ingestion
# ----------------------------------------------------------------------------------------

# Load PDF files using PyPDFLoader
def load_pdf_documents():

    # List of text of each pdf file
    pdf_documents = []

    # Check if data folder exists
    if not data_folder_path.exists():
        logger.error(f"Data folder {data_folder_path} does not exist.")
    else:
        # Load paths to each pdf file in data file.
        pdf_files = list(data_folder_path.glob("*.pdf"))

        # Check if there is any pdf files in the data directory
        if not pdf_files:
            logger.error(f"Data folder {data_folder_path} does not contain any PDF files.")
        else:
            for pdf_file in pdf_files:
                loader = PyPDFLoader(str(pdf_file))
                document = loader.load()
                pdf_documents.extend(document)

        logger.info(f"Loaded {len(pdf_documents)} pages in total.")

    return pdf_documents

# Function made to split pdf documents into chunks for ingestion.
def split_pdf_documents(pdf_documents):

    # Create text splitter with chunk size and overlap from constants
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_overlap=chunk_overlap,
        chunk_size=chunk_size,
    )

    # Get document chunks
    document_chunks = text_splitter.split_documents(pdf_documents)

    logger.info(f"Splitted total {len(document_chunks)} documents chunks.")
    return document_chunks

if __name__ == "__main__":
    pdf_documents = load_pdf_documents()
    document_chunks = split_pdf_documents(pdf_documents)
