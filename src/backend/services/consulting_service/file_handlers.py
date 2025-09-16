"""
File handlers module for document processing.

This module provides functions for processing various document file types,
extracting metadata, and chunking the documents for use in a retrieval-augmented
generation (RAG) system.

Typical usage:
    from file_handlers import process_file
    textss = file_handlers('path/to/document.pdf')
    # texts can then be add to a vector database

"""


import os
import logging
from typing import List, Dict, Any, Optional, Union, Tuple
from pathlib import Path

# Document loaders
from langchain.document_loaders import (
    PyPDFLoader,
    Docx2txtLoader,
    TextLoader,
    UnstructuredHTMLLoader,
    CSVLoader,
    UnstructuredMarkdownLoader
)
from langchain.document_loaders.base import BaseLoader
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Configuration logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Get chunking parameters from environment variables with defaults
DEFAULT_CHUNK_SIZE = int(os.environ.get('RAG_CHUNK_SIZE', '1000'))
DEFAULT_CHUNK_OVERLAP = int(os.environ.get('RAG_CHUNK_OVERLAP', '100'))
DEFAULT_SEPARATORS = os.environ.get(
    'RAG_SEPARATORS',
    '\n\n,\n,.,!,?,;,:,\t, ,'
).split(',')

class UnsupportedFileTypeError(ValueError):
    """Exception raised when an unsupported file type is encountered."""
    pass

class DocumentProcessingError(Exception):
    """Exception raised when document processing fails."""
    pass

def get_document_loader(file_path: str) -> BaseLoader:
    """
    Get the appropriate document loader based on the file extension.
    
    Args:
        file_path (str): Path to the document file.
    
    Returns:
        BaseLoader: An instance of the appropriate document loader.
    
    Raises:
        UnsupportedFileTypeError: If the file type is not supported.
    """
    file_path = str(file_path) # Convert Path objects to string if needed
    file_extension = os.path.splitext(file_path)[1].lower()

    # Map file extensions to loaders
    loaders = {
        '.pdf': PyPDFLoader,
        '.docx': Docx2txtLoader,
        '.txt': TextLoader,
        '.html': UnstructuredHTMLLoader,
        '.csv': CSVLoader,
        '.md': UnstructuredMarkdownLoader,
    }

    loader_class = loaders.get(file_extension)
    if not loader_class:
        supported_formats = ', '.join(loaders.keys())
        raise UnsupportedFileTypeError(
            f"Unsupported file type: {file_extension}. Supported formats: {supported_formats}"
        )
    
    return loader_class(file_path)


def extract_metadata(file_path: str) -> Dict[str, Any]:
    """Extract metadata from a file.
    
    Args:
        file_path: Path to the document file
        
    Returns:
        Dictionary containing metadata about the file
    """

    file_stats = os.stat(file_path)
    return {
        'source': os.path.basename(file_path),
        'filename': os.path.basename(file_path),
        'file_path': file_path,
        'file_type': os.path.splitext(file_path)[1].lower(),
        'file_size': file_stats.st_size,
        'created_at': file_stats.st_ctime,
        'modified_at': file_stats.st_mtime
    }


def file_handler(
    file_path: Union[str, Path],
    chunk_size: Optional[int] = None,
    chunk_overlap: Optional[int] = None,
    separators: Optional[List[str]] = None,
    include_metadata: bool = True
) -> List[Document]:
    """
    Process a document file, extracting its content and metadata.
    
    Args:
        file_path: Path to the document file
        chunk_size: Size of text chunks to split the document into
        chunk_overlap: Overlap between consecutive text chunks
        separators: List of separator strings to use for splitting
        include_metadata: Whether to include file metadata in the output
        
    Returns:
        List of Document objects, each containing a chunk of the document's content
        and optionally its metadata
    """

    file_path_str = str(file_path) # Convert Path objects to string if needed
    
    # Check if file exists
    if not os.path.exists(file_path_str):
        raise FileNotFoundError(f"File not found: {file_path_str}")
    
    # Use provided parameters or defaults
    chunk_size = chunk_size or DEFAULT_CHUNK_SIZE
    chunk_overlap = chunk_overlap or DEFAULT_CHUNK_OVERLAP
    separators = separators or DEFAULT_SEPARATORS

    try:
        # Get document loader
        loader = get_document_loader(file_path_str)

        # Load document content
        logger.info(f"Loading document: {file_path_str}")   
        documents = loader.load()
        logger.info(f"Document loaded successfully. Number of pages: {len(documents)} Loaded {len(documents)} document(s) from {file_path_str}")

        # Add file metadata to each document if requested
        if include_metadata:
            file_metadata = extract_metadata(file_path_str)
            for doc in documents:
                doc.metadata.update(file_metadata)

        # Split documents into chunks
        logger.info(f"Splitting text with chunk_size={chunk_size}, overlap={chunk_overlap}")
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=separators
        )
        texts = text_splitter.split_documents(documents)
        
        # Log success
        logger.info(f"Processed {file_path_str}: {len(texts)} chunks created")
        return texts   

    except UnsupportedFileTypeError:
        # logger.error(f"Unsupported file type error: {e}")
        raise
    except DocumentProcessingError:
        # logger.error(f"Document processing error: {e}")
        raise
    except Exception as e:
        # Wrap other exceptions in a DocumentProcessingError
        error_msg = f"Error processing file {file_path_str}: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise DocumentProcessingError(error_msg) from e

    
def files_handler(
    file_paths: List[Union[str, Path]],
    chunk_size: Optional[int] = None,
    chunk_overlap: Optional[int] = None,
    separators: Optional[List[str]] = None,
    include_metadata: bool = True,
    parallel: bool = True
) -> List[Document]:
    """
    Process multiple document files, extracting their content and metadata.
        
    Args:
        file_paths: List of paths to document files
        chunk_size: Size of text chunks to split the documents into
        chunk_overlap: Overlap between consecutive text chunks
        separators: List of separator strings to use for splitting
        include_metadata: Whether to include file metadata in the output
        parallel: Whether to process files in parallel
            
    Returns:
        List of Document objects, each containing a chunk of the document's content
        and optionally its metadata
    """
    all_texts = []
    errors = []

    if parallel:
        try:
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future_to_file = {}
                for file_path in file_paths:
                    future = executor.submit(
                        file_handler, 
                        file_path, 
                        chunk_size, 
                        chunk_overlap, 
                        separators, 
                        include_metadata
                    )
                    future_to_file[future] = file_path

                for future in concurrent.futures.as_completed(future_to_file):
                    file_path = future_to_file[future]
                    try:
                        texts = future.result()
                        all_texts.extend(texts)
                        logger.info(f"Processed {file_path}: {len(texts)} chunks created")
                    except Exception as e:
                        errors.append((file_path, str(e)))
                        logger.error(f"Error processing {file_path}: {str(e)}")
        except ImportError:
            logger.warning("concurrent.futures not available, falling back to sequential processing")
            parallel = False
        
    if not parallel:
        for file_path in file_paths:
            try:
                texts = file_handler(
                    file_path,
                    chunk_size,
                    chunk_overlap,
                    separators,
                    include_metadata
                )
                all_texts.extend(texts)
            except Exception as e:
                errors.append(str(e))
                logger.error(f"Error processing {file_path}: {str(e)}")

    if errors:
        error_msg = "\n".join([f"{path}: {err}" for path, err in errors])
        logger.error(f"Errors occurred while processing files: \n{error_msg}")
        if len(errors) == len(file_paths):
            raise DocumentProcessingError(f"All files failed to process: \n{error_msg}")

    return all_texts


if __name__ == "__main__":
    import argparse
    import glob
    import json
    
    parser = argparse.ArgumentParser(description="Process documents for RAG applications")
    parser.add_argument(
        "files", nargs="+", help="Files or glob patterns to process"
    )
    parser.add_argument(
        "--chunk-size", type=int, default=DEFAULT_CHUNK_SIZE,
        help=f"Size of text chunks (default: {DEFAULT_CHUNK_SIZE})"
    )
    parser.add_argument(
        "--chunk-overlap", type=int, default=DEFAULT_CHUNK_OVERLAP,
        help=f"Overlap between chunks (default: {DEFAULT_CHUNK_OVERLAP})"
    )
    parser.add_argument(
        "--output", "-o", help="Output file for processed chunks (JSON format)"
    )
    parser.add_argument(
        "--no-metadata", action="store_true", help="Don't include file metadata in chunks"
    )
    parser.add_argument(
        "--sequential", action="store_true", help="Process files sequentially (no parallelism)"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Configure logging based on verbosity
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Expand glob patterns to get all matching files
    all_files = []
    for pattern in args.files:
        if '*' in pattern or '?' in pattern:
            matched_files = glob.glob(pattern, recursive=True)
            if not matched_files:
                logger.warning(f"No files matched pattern: {pattern}")
            all_files.extend(matched_files)
        else:
            all_files.append(pattern)
    
        if not all_files:
            logger.error("No files to process")
            parser.print_help()
            exit(1)
        
        logger.info(f"Processing {len(all_files)} files")
    
    try:
        # Process all files
        chunks = process_files(
            file_paths=all_files,
            chunk_size=args.chunk_size,
            chunk_overlap=args.chunk_overlap,
            include_metadata=not args.no_metadata,
            parallel=not args.sequential
        )
        
        logger.info(f"Created {len(chunks)} total chunks from {len(all_files)} files")
        
        # Output results
        if args.output:
            # Convert Document objects to dictionaries for JSON serialization
            serializable_chunks = [
                {"text": doc.page_content, "metadata": doc.metadata}
                for doc in chunks
            ]
            
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(serializable_chunks, f, indent=2, default=str)
            logger.info(f"Saved {len(chunks)} chunks to {args.output}")
        else:
            # Print summary to console
            print(f"\nProcessed {len(all_files)} files into {len(chunks)} chunks")
            for i, chunk in enumerate(chunks[:3]):
                print(f"\nChunk {i+1}/{min(3, len(chunks))} (sample):")
                print(f"Text: {chunk.page_content[:100]}...")
                print(f"Metadata: {json.dumps(chunk.metadata, default=str)}")
            
            if len(chunks) > 3:
                print(f"\n... and {len(chunks) - 3} more chunks")
    
    except Exception as e:
        logger.error(f"Processing failed: {str(e)}")
        exit(1)
    








