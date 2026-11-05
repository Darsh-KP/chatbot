import hashlib
import logging
from pathlib import Path
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from models.ChunkModel import ChunkModel
from exceptions import FailedToReadTagException
import re

# -----------------------------------------------------------------
# This service is used for document ingestion, embedding and storing
# of the model's knowledge corpus in a VectorDB
# -----------------------------------------------------------------

# ----------------------- Constants -------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_FOLDER_PATH = PROJECT_ROOT / "data"
PAGES_FOLDER_PATH = DATA_FOLDER_PATH / "pages"
PERSIST_DIRECTORY = str(PROJECT_ROOT / "chroma_db")

CHUNK_SIZE = 900
CHUNK_OVERLAP = 150
BATCH_SIZE = 16
SEPARATORS = ["\n== ", "\n=== ", "\n==== ", "\n\n", "\n", " "]

# ----------------------- Logger -------------------------------

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
LOGGER = logging.getLogger(__name__)

# ----------------------- Vector Store -------------------------------

# The ChromaDB vector store
VECTOR_STORE: dict[str, Chroma] = {}

# ----------------------- Embedding Model ---------------------------

EMBEDDING_MODEL = OllamaEmbeddings(model="nomic-embed-text")

# ----------------------- Collection Functions ------------------------

def create_or_get_collection(collection_name: str) -> Chroma:
    """Returns collection by name if exists, creates new Chroma DB otherwise."""
    if collection_name not in VECTOR_STORE:
        VECTOR_STORE[collection_name] = Chroma(
            persist_directory=PERSIST_DIRECTORY,
            collection_name=collection_name,
            embedding_function=EMBEDDING_MODEL,
        )
    return VECTOR_STORE[collection_name]

def search_collection(
    collection_name: str, query: str, k: int = 5
) -> list[tuple[Document, float]]:
    """Given a query and collection name, returns the K most similar documents"""
    collection = create_or_get_collection(collection_name)
    return collection.similarity_search_with_score(query, k)

# ----------------------- ADOC Tag Extraction -------------------------------

def _extract_adoc_metadata(file_path: Path) -> list[str]:
    """Attempts to extract header tags from ascii document."""
    try:
        lines = file_path.read_text(encoding="utf-8").splitlines()[:20]
        tags: list[str] = []

        for line in lines:
            tag_match = re.match(r"^:tags:\s*(.*)", line, re.IGNORECASE)
            if tag_match:
                raw_tags = tag_match.group(1).split(",")
                tags.extend([t.strip() for t in raw_tags if t.strip()])

    except Exception as e:
        LOGGER.error(f"Failed to extract tags from {file_path}: {e}")
        raise FailedToReadTagException(f"Could not read tags from {file_path}") from e

    return tags

def _get_tags(adoc_path: Path) -> list[str]:
    """Gets tags for specific ascii document, those being path names and header tags if present."""
    adoc_path = adoc_path.resolve()

    # Generate path-based tags automatically
    relative_path = adoc_path.relative_to(DATA_FOLDER_PATH)
    path_tags = list(relative_path.parts[:-1])

    try:
        # Extract any explicit tags from the adoc file header
        header_tags = _extract_adoc_metadata(adoc_path)

    # Don't need to really handle exception since the path tags can be used instead.
    except FailedToReadTagException:
        header_tags = []

    # Preserve path/header order while removing duplicates.
    return list(dict.fromkeys(path_tags + header_tags))

# ----------------------- ADOC Parsing Helper Functions -------------------------------

def _clean_adoc(text: str) -> str:
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
    """Gets title of document, if not falls back to default fallback argument."""
    for line in text.splitlines():
        if line.startswith("="):
            return line.lstrip("=").strip() or fallback
    return fallback

# ----------------------- ADOC Ingestion -------------------------------

def ingest_adoc_directory(collection_name: str) -> int:
    """Ingests Ascii Docs, embeds them and saves vectors to local Chroma DB
    Returns number of document chunks ingested."""

    # Get the target Chroma collection
    collection = create_or_get_collection(collection_name)

    # Raise an exception if the data folder can not be found.
    if not PAGES_FOLDER_PATH.exists():
        logging.error(f"{PAGES_FOLDER_PATH} does not exist")
        raise FileNotFoundError(f"{PAGES_FOLDER_PATH} does not exist")

    # Recursively search through page folder for all adoc files
    adoc_files = sorted(
        list(PAGES_FOLDER_PATH.glob("**/*.adoc"))
        + list(PAGES_FOLDER_PATH.glob("**/*.asciidoc"))
    )

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
            raw_text = adoc_file.read_text(encoding="utf-8", errors="replace")
            cleaned_text = _clean_adoc(raw_text)
            if not cleaned_text:
                continue
            title = _document_title(cleaned_text, adoc_file.stem)
            docs = [Document(page_content=cleaned_text, metadata={"source": str(adoc_file)})]

            # Get chunks using the text splitter
            chunks = text_splitter.split_documents(docs)
            relative = adoc_file.relative_to(DATA_FOLDER_PATH).as_posix()
            digest = hashlib.sha1(relative.encode()).hexdigest()[:10]
            tags = _get_tags(adoc_file)

            # Go through each chunk convert to LangChain Document
            for i, chunk in enumerate(chunks):
                chunk_id = f"{digest}_chunk_{i}"

                # make a chunk model with an id, the text, file name and tags
                chunk_model = ChunkModel(
                    id=chunk_id,
                    text=chunk.page_content,
                    file=str(adoc_file),
                    tags=tags
                )

                doc = Document(
                    page_content=chunk_model.text,
                    metadata={
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
        for start in range(0, len(document_chunks), BATCH_SIZE):
            end = start + BATCH_SIZE
            collection.add_documents(
                documents=document_chunks[start:end],
                ids=chunk_ids[start:end],
            )
        LOGGER.info(f"Successfully ingested {len(document_chunks)} chunks from {DATA_FOLDER_PATH}")
        return len(document_chunks)

    LOGGER.info(f"No chunks found to ingest from {DATA_FOLDER_PATH}")
    return 0
