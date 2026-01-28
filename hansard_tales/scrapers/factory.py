"""
Scraper factory for creating appropriate scrapers based on document type.

This module provides a factory function to instantiate the correct scraper
for a given document type.
"""

from hansard_tales.scrapers.base import BaseScraper
from hansard_tales.scrapers.hansard import HansardScraper
from hansard_tales.scrapers.votes import VotesScraper
from hansard_tales.models.base import DocumentType
from hansard_tales.config.settings import ScraperConfig


def create_scraper(document_type: DocumentType, config: ScraperConfig) -> BaseScraper:
    """
    Factory function to create appropriate scraper for document type.
    
    This function instantiates the correct scraper class based on the
    document type. Currently supports Hansard and Votes & Proceedings.
    More scrapers will be added in later phases.
    
    Args:
        document_type: Type of document to scrape
        config: Scraper configuration
        
    Returns:
        Appropriate scraper instance
        
    Raises:
        ValueError: If no scraper exists for the document type
        
    Example:
        >>> config = ScraperConfig()
        >>> scraper = create_scraper(DocumentType.HANSARD, config)
        >>> documents = scraper.scrape(Chamber.NATIONAL_ASSEMBLY)
    """
    scrapers = {
        DocumentType.HANSARD: HansardScraper,
        DocumentType.VOTES: VotesScraper,
        # More scrapers will be added in later phases:
        # DocumentType.BILL: BillScraper,
        # DocumentType.QUESTION: QuestionScraper,
        # DocumentType.PETITION: PetitionScraper,
        # etc.
    }
    
    scraper_class = scrapers.get(document_type)
    if not scraper_class:
        raise ValueError(
            f"No scraper available for document type: {document_type}. "
            f"Available types: {', '.join(str(t.value) for t in scrapers.keys())}"
        )
    
    return scraper_class(config)
