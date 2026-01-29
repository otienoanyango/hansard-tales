#!/usr/bin/env python3
"""
Example script demonstrating Prometheus metrics integration.

This script shows how to:
1. Start the Prometheus metrics server
2. Use the track_processing_time decorator
3. Update metrics manually
4. Access metrics via HTTP endpoint

Run this script and then visit http://localhost:9090/metrics to see the metrics.
"""

import random
import time
from pathlib import Path

from hansard_tales.monitoring.metrics import (
    error_count,
    queue_depth,
    start_metrics_server,
    track_processing_time,
    vector_db_size,
)


# Example 1: Using the decorator
@track_processing_time("hansard", "national_assembly")
def process_hansard_document(pdf_path: Path) -> dict:
    """
    Example function that processes a Hansard document.

    The decorator automatically tracks:
    - Processing time (histogram)
    - Success/failure count (counter)
    - Errors (counter)
    """
    print(f"Processing {pdf_path}...")

    # Simulate processing time
    time.sleep(random.uniform(0.1, 0.5))

    # Simulate occasional errors
    if random.random() < 0.1:
        raise ValueError("Simulated processing error")

    return {"status": "success", "statements": random.randint(10, 100)}


# Example 2: Manual metrics updates
def update_queue_metrics():
    """Example of manually updating gauge metrics."""
    # Simulate queue depth changes
    for doc_type in ["hansard", "votes", "bills"]:
        depth = random.randint(0, 50)
        queue_depth.labels(document_type=doc_type).set(depth)
        print(f"Queue depth for {doc_type}: {depth}")


def update_vector_db_metrics():
    """Example of updating vector database size metrics."""
    # Simulate vector DB size
    for collection in ["hansard", "bills", "questions"]:
        size = random.randint(1000, 10000)
        vector_db_size.labels(collection=collection).set(size)
        print(f"Vector DB size for {collection}: {size}")


# Example 3: Manual error tracking
def track_custom_error(component: str, error_type: str):
    """Example of manually tracking errors."""
    error_count.labels(component=component, error_type=error_type).inc()
    print(f"Tracked error: {component}/{error_type}")


def main():
    """Main example function."""
    print("Starting Prometheus metrics example...")
    print("=" * 60)

    # Start the metrics server
    print("\n1. Starting metrics server on port 9090...")
    start_metrics_server(port=9090)
    print("   ✓ Metrics server started")
    print("   → Visit http://localhost:9090/metrics to see metrics")

    # Give the server a moment to start
    time.sleep(1)

    print("\n2. Processing documents with decorator...")
    # Process some documents
    for i in range(10):
        pdf_path = Path(f"test_document_{i}.pdf")
        try:
            result = process_hansard_document(pdf_path)
            print(f"   ✓ Processed {pdf_path}: {result['statements']} statements")
        except ValueError as e:
            print(f"   ✗ Error processing {pdf_path}: {e}")

        time.sleep(0.2)

    print("\n3. Updating queue depth metrics...")
    update_queue_metrics()

    print("\n4. Updating vector DB size metrics...")
    update_vector_db_metrics()

    print("\n5. Tracking custom errors...")
    track_custom_error("scraper", "NetworkError")
    track_custom_error("processor", "ParseError")
    track_custom_error("storage", "DatabaseError")

    print("\n" + "=" * 60)
    print("Example complete!")
    print("\nMetrics are now available at: http://localhost:9090/metrics")
    print("\nExample queries you can run in Prometheus:")
    print("  - rate(documents_processed_total[5m])")
    print("  - histogram_quantile(0.95, rate(document_processing_seconds_bucket[5m]))")
    print("  - rate(errors_total[5m])")
    print("  - processing_queue_depth")
    print("  - vector_db_documents_total")
    print("\nPress Ctrl+C to stop the metrics server...")

    # Keep the server running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\nShutting down...")


if __name__ == "__main__":
    main()
