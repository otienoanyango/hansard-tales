"""Web scrapers for parliament.go.ke."""

from hansard_tales.scrapers.base import BaseScraper, DataCollectionError, ScrapedDocument
from hansard_tales.scrapers.factory import create_scraper
from hansard_tales.scrapers.hansard import HansardScraper
from hansard_tales.scrapers.mp import MPData, MPScraper
from hansard_tales.scrapers.votes import VotesScraper

__all__ = [
    "BaseScraper",
    "ScrapedDocument",
    "DataCollectionError",
    "HansardScraper",
    "VotesScraper",
    "MPScraper",
    "MPData",
    "create_scraper",
]
