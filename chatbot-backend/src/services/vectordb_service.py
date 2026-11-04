import hashlib
import logging
from pathlib import Path
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from ..models.ChunkModel import ChunkModel
import re

# -----------------------------------------------------------------
# This service is used for document ingestion, embedding and storing
# of the model's knowledge corpus in a VectorDB
# -----------------------------------------------------------------

# ----------------------- Constants -------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_FOLDER_PATH = PROJECT_ROOT / "data"
PAGES_FOLDER_PATH = DATA_FOLDER_PATH / "pages"
PERSISTY_DIRECTORY = str(PROJECT_ROOT / "chroma_db")

CHUNK_SIZE = 900
CHUNK_OVERLAP = 150
SEPARATORS = ["\n== ", "\n=== ", "\n==== ", "\n\n", "\n", " "]

# ----------------------- Logger -------------------------------

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
LOGGER = logging.getLogger(__name__)

# ----------------------- Vector Store -------------------------------

# The ChromaDB vector store
VECTOR_STORE: dict[str, Chroma] = {}

# ----------------------- Embedding Model ---------------------------

# TODO: Actually download embedding model
EMBEDDING_MODEL = OllamaEmbeddings(model="nomic-embed-text")


# ----------------------- Collection Functions ------------------------

# Function used to create collection
def create_or_get_collection(collection_name: str):

    if collection_name not in VECTOR_STORE:
        VECTOR_STORE[collection_name] = Chroma(
            persist_directory=PERSISTY_DIRECTORY,
            collection_name=collection_name,
            embedding_function=EMBEDDING_MODEL
        )
    return VECTOR_STORE[collection_name]

# Function that searches collection, returns k most relevant results
def search_collection(collection_name:str, query:str, k:int=5):

    # Get collection
    collection = create_or_get_collection(collection_name)

    # Perform the similarity search
    results = collection.similarity_search_with_score(query, k)

    return results

# ----------------------- ADOC Tag Extraction -------------------------------

def extract_adoc_metadata(file_path: Path) -> list[str]:
    tags = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            # Read the first 20 lines to check for attributes/headers
            lines = [f.readline() for _ in range(20)]

        for line in lines:
            # Look for AsciiDoc tag attributes, e.g., ":tags: python, chroma"
            tag_match = re.match(r"^:tags:\s*(.*)", line, re.IGNORECASE)
            if tag_match:
                # Split comma-separated tags and strip whitespace
                raw_tags = tag_match.group(1).split(",")
                tags.extend([t.strip() for t in raw_tags if t.strip()])

    except Exception as e:
        # TODO Make a more descriptive exception
        LOGGER.error(f"Failed to extract tags from {file_path}: {e}")
        raise e

    return tags

def get_tags(adoc_path: Path) -> list[str]:
    adoc_path = adoc_path.resolve()

    # Generate path-based tags automatically
    relative_path = adoc_path.relative_to(DATA_FOLDER_PATH)
    path_tags = list(relative_path.parts[:-1])

    header_tags = None
    try:
        # Extract any explicit tags from the adoc file header
        header_tags = extract_adoc_metadata(adoc_path)
    except Exception:
        # TODO Do something with this error ;-;
        pass

    # Combine them into a master list of tags for this file
    base_tags = path_tags if header_tags is None else list(set(path_tags + header_tags))
    return base_tags


def clean_adoc(text: str) -> str:
    """Remove AsciiDoc noise while preserving headings and readable content."""
    lines = []
    for line in text.replace("\r\n", "\n").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith(":") or stripped.startswith("//"):
            continue
        if stripped.startswith("image::") or stripped.startswith("include::"):
            continue
        lines.append(line.rstrip())
    return "\n".join(lines).strip()


def _document_title(text: str, fallback: str) -> str:
    for line in text.splitlines():
        if line.startswith("="):
            return line.lstrip("=").strip() or fallback
    return fallback

# ----------------------- ADOC Ingestion -------------------------------

def ingest_adoc_directory(collection_name: str):

    # Get the target Chroma collection
    collection = create_or_get_collection(collection_name)

    # Raise an exception if the data folder can not be found.
    if not PAGES_FOLDER_PATH.exists():
        logging.error(f"{PAGES_FOLDER_PATH} does not exist")
        raise FileNotFoundError(f"{PAGES_FOLDER_PATH} does not exist")

    # Recursively search through page folder for all adoc files
    adoc_files = list(PAGES_FOLDER_PATH.glob("**/*.adoc")) + list(PAGES_FOLDER_PATH.glob("**/*.asciidoc"))

    document_chunks = []
    chunk_ids = []

    # Split text into chunks (separators should, split apart headings, lists, etc.)
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=SEPARATORS
    )

    # Process each adoc file
    for adoc_file in adoc_files:
        LOGGER.debug(f"Loading {adoc_file}")
        try:
            # Create UnstructuredFileLoader to load specific adoc_file
            raw_text = adoc_file.read_text(encoding="utf-8", errors="replace")
            cleaned_text = clean_adoc(raw_text)
            if not cleaned_text:
                continue
            title = _document_title(cleaned_text, adoc_file.stem)
            docs = [Document(page_content=cleaned_text, metadata={"source": str(adoc_file)})]

            # Get chunks using the text splitter
            chunks = text_splitter.split_documents(docs)

            # Go through each chunk convert to LangChain Document
            for i, chunk in enumerate(chunks):
                relative = adoc_file.relative_to(DATA_FOLDER_PATH).as_posix()
                digest = hashlib.sha1(relative.encode()).hexdigest()[:10]
                chunk_id = f"{digest}_chunk_{i}"

                # make a chunk model with an id, the text, file name and tags
                chunk_model = ChunkModel(
                    id=chunk_id,
                    text=chunk.page_content,
                    file=str(adoc_file),
                    tags=get_tags(adoc_file)
                )

                doc = Document(
                    page_content=chunk_model.text,
                    metadata={
                        "file": chunk_model.file,
                        "source": chunk_model.file,
                        "title": title,
                        "chunk_index": i,
                        "tags": ",".join(chunk_model.tags or [])
                    }
                )

                # Add the current chunk to the list of chunks
                document_chunks.append(doc)
                chunk_ids.append(chunk_model.id)

        except Exception as e:
            LOGGER.error(f"{adoc_file} could not be opened: {str(e)}")

    # Ingest into Chroma if chunks were found
    if document_chunks:
        collection.add_documents(documents=document_chunks, ids=chunk_ids)
        LOGGER.info(f"Successfully ingested {len(document_chunks)} chunks from {DATA_FOLDER_PATH}")
        return len(document_chunks)

    LOGGER.info(f"No chunks found to ingest from {DATA_FOLDER_PATH}")
    return 0
