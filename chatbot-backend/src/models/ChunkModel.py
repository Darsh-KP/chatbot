from typing import Annotated, Optional
from pydantic import BaseModel, Field


class ChunkModel(BaseModel):
    # Use a string for unique chunk IDs (e.g., "my_guide_chunk_0")
    id: Annotated[str, Field(description="Unique identifier for the chunk")]

    # The actual text content that gets embedded and searched
    text: Annotated[str, Field(description="The text content of the chunk")]

    # Source file path
    file: Annotated[str, Field(description="Path to the source .adoc file")]

    # Optional tags for filtering or metadata
    tags: Annotated[Optional[list[str]], Field(default=None, description="Tags associated with the document")]