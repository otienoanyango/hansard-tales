"""Web scrapers for parliament.go.ke."""

from hansard_tales.scrapers.base import BaseScraper, ScrapedDocument, DataCollectionError
from hansard_tales.scrapers.hansard import HansardScraper
from hansard_tales.scrapers.votes import VotesScraper
from hansard_tales.scrapers.factory import create_scraper

__all__ = [
    'BaseScraper',
    'ScrapedDocument',
    'DataCollectionError',
    'HansardScraper',
    'VotesScraper',
    'create_scraper',
]
