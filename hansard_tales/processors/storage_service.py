"""
Document storage service for storing processed documents in SQL and vector databases.

This module provides the DocumentStorageService class for managing document storage
across both relational (SQL) and vector databases with embedding generation.
"""

from typing import Optional
from datetime import datetime
from hansard_tales.processors.pdf_processor import ProcessedPDF
from hansard_tales.models.base import Document


class DocumentStorageService:
    """
    Service for storing processed documents in both SQL and vector databases.
    
    This service coordinates storage across multiple backends:
    - SQL database (PostgreSQL/SQLite) for structured data
    - Vector database (Qdrant/ChromaDB) for semantic search
    - Embedding generation for document vectorization
    
    Attributes:
        db: SQLAlchemy database session
        vector_db: Vector database adapter (VectorDB interface)
        embedding_generator: Embedding generator for text vectorization
        
    Example:
        >>> from hansard_tales.vector_db.factory import create_vector_db
        >>> from hansard_tales.vector_db.embedding import EmbeddingGenerator
        >>> 
        >>> storage = DocumentStorageService(
        ...     db_session=session,
        ...     vector_db=create_vector_db(config),
        ...     embedding_generator=EmbeddingGenerator(config)
        ... )
        >>> doc_id = storage.store_document(processed_pdf, document)
    """
    
    def __init__(
        self,
        db_session,
        vector_db,
        embedding_generator
    ):
        """
        Initialize document storage service.
        
        Args:
            db_session: SQLAlchemy database session
            vector_db: Vector database adapter implementing VectorDB interface
            embedding_generator: Embedding generator for text vectorization
        """
        self.db = db_session
        self.vector_db = vector_db
        self.embedding_generator = embedding_generator
    
    def store_document(
        self,
        processed_pdf: ProcessedPDF,
        document: Document
    ) -> str:
        """
        Store document in both SQL and vector databases.
        
        This method:
        1. Stores structured data in SQL database
        2. Generates embeddings for document text
        3. Stores embeddings in vector database with metadata
        
        Args:
            processed_pdf: Processed PDF with extracted text and metadata
            document: Document model with metadata
            
        Returns:
            Document ID as string
            
        Example:
            >>> doc_id = storage.store_document(processed_pdf, document)
            >>> print(f"Stored document: {doc_id}")
        """
        # Import here to avoid circular dependency
        from hansard_tales.database.models import DocumentORM
        
        # Store in SQL database
        doc_orm = DocumentORM(
            id=document.id,
            type=document.type.value,
            chamber=document.chamber.value,
            title=document.title,
            date=document.date,
            session_id=document.session_id,
            parliament_term=document.parliament_term,
            source_url=document.source.source_url,
            source_hash=document.source.source_hash,
            download_date=document.source.download_date,
            vector_doc_id=document.vector_doc_id,
            metadata=document.metadata,
            created_at=document.created_at,
            updated_at=document.updated_at
        )
        self.db.add(doc_orm)
        self.db.commit()
        
        # Generate embedding for full document text
        full_text = " ".join([block.text for block in processed_pdf.text_blocks])
        embedding = self.embedding_generator.generate(full_text)
        
        # Store in vector DB
        self.vector_db.insert(
            collection="documents",
            id=document.vector_doc_id,
            vector=embedding,
            payload={
                "document_id": str(document.id),
                "document_type": document.type.value,
                "chamber": document.chamber.value,
                "date": document.date.isoformat(),
                "session_id": document.session_id or "",
                "parliament_term": document.parliament_term,
                "source_url": document.source.source_url,
                "source_hash": document.source.source_hash,
            },
            text=full_text
        )
        
        return str(document.id)
    
    def is_duplicate(self, source_hash: str) -> bool:
        """
        Check if document already exists by source hash.
        
        Args:
            source_hash: SHA256 hash of source PDF
            
        Returns:
            True if document with this hash already exists
            
        Example:
            >>> if storage.is_duplicate(pdf_hash):
            ...     print("Document already processed")
        """
        from hansard_tales.database.models import DocumentORM
        
        existing = self.db.query(DocumentORM).filter(
            DocumentORM.source_hash == source_hash
        ).first()
        return existing is not None
    
    def get_document(self, document_id: str) -> Optional[Document]:
        """
        Retrieve document by ID from SQL database.
        
        Args:
            document_id: UUID of document to retrieve
            
        Returns:
            Document model if found, None otherwise
            
        Example:
            >>> doc = storage.get_document(doc_id)
            >>> if doc:
            ...     print(f"Found: {doc.title}")
        """
        from hansard_tales.database.models import DocumentORM
        from hansard_tales.models.base import DocumentType, Chamber, SourceReference
        
        doc_orm = self.db.query(DocumentORM).filter(
            DocumentORM.id == document_id
        ).first()
        
        if not doc_orm:
            return None
        
        return Document(
            id=doc_orm.id,
            type=DocumentType(doc_orm.type),
            chamber=Chamber(doc_orm.chamber),
            title=doc_orm.title,
            date=doc_orm.date,
            session_id=doc_orm.session_id,
            parliament_term=doc_orm.parliament_term,
            source=SourceReference(
                source_url=doc_orm.source_url,
                source_hash=doc_orm.source_hash,
                download_date=doc_orm.download_date
            ),
            vector_doc_id=doc_orm.vector_doc_id,
            metadata=doc_orm.metadata,
            created_at=doc_orm.created_at,
            updated_at=doc_orm.updated_at
        )
