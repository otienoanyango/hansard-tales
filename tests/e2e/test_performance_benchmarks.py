"""
Performance benchmarking tests for Phase 1 analysis pipeline.

Tests performance characteristics and identifies bottlenecks:
- Benchmark Hansard processing time
- Benchmark LLM API calls
- Benchmark vector DB queries
- Benchmark site generation
- Optimize bottlenecks
"""

import tempfile
import time
from datetime import UTC, date, datetime
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from hansard_tales.analysis.context_retriever import ContextRetriever
from hansard_tales.analysis.filler_detector import FillerDetector
from hansard_tales.analysis.llm_analyzer import LLMAnalyzer
from hansard_tales.analysis.mp_identifier import MPIdentifier
from hansard_tales.analysis.statement_segmenter import Statement, StatementSegmenter
from hansard_tales.database.models import MPORM, Base, SessionORM, StatementORM
from hansard_tales.models import Chamber
from hansard_tales.site.generator import StaticSiteGenerator
from hansard_tales.vector_db import ChromaDBAdapter


@pytest.fixture
def temp_db():
    """Create temporary database with sample data."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Add sample MPs
    for i in range(50):  # Add 50 MPs for realistic testing
        mp = MPORM(
            name=f"Hon. MP {i}",
            clean_name=f"MP {i}",
            constituency=f"Constituency {i}",
            party="UDA" if i % 2 == 0 else "ODM",
            chamber=Chamber.NATIONAL_ASSEMBLY.value,
            status="Elected",
            parliament_term=13,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        session.add(mp)

    # Add sample session
    test_session = SessionORM(
        date=date(2025, 11, 4),
        session_type="afternoon",
        chamber=Chamber.NATIONAL_ASSEMBLY.value,
        parliament_term=13,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    session.add(test_session)

    session.commit()
    yield session
    session.close()


@pytest.fixture
def temp_vector_db():
    """Create temporary vector database."""
    with tempfile.TemporaryDirectory() as tmpdir:
        vector_db = ChromaDBAdapter(persist_directory=tmpdir)
        vector_db.create_collection("statements", dimension=384)
        yield vector_db


@pytest.fixture
def temp_output_dir():
    """Create temporary output directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def large_hansard_text():
    """Generate large Hansard text for performance testing."""
    # Generate text with 100 statements
    statements = []
    for i in range(100):
        mp_num = i % 50
        statements.append(
            f"""
Hon. MP {mp_num} (Constituency {mp_num}, {"UDA" if mp_num % 2 == 0 else "ODM"}):
Mr. Speaker, I rise to contribute to this important debate. This is statement number {i}.
We need to address the critical issues facing our nation including economic development,
healthcare reform, education improvement, and infrastructure development. The proposed
legislation will have significant impact on our constituents and requires careful consideration.
"""
        )

    return "\n\n".join(statements)


class TestHansardProcessingPerformance:
    """Test Hansard processing performance."""

    def test_benchmark_segmentation_performance(self, temp_db, large_hansard_text):
        """Benchmark statement segmentation performance."""
        mp_identifier = MPIdentifier(temp_db)
        segmenter = StatementSegmenter(mp_identifier)

        # Warm up
        segmenter.segment(large_hansard_text[:1000], session_id="warmup")

        # Benchmark
        start_time = time.time()
        statements = segmenter.segment(large_hansard_text, session_id="test")
        segmentation_time = time.time() - start_time

        # Verify performance
        assert len(statements) >= 50  # Should segment many statements
        assert segmentation_time < 5.0  # Should complete in under 5 seconds

        # Calculate throughput
        statements_per_second = len(statements) / segmentation_time
        assert statements_per_second > 10  # Should process at least 10 statements/sec

        print("\nSegmentation Performance:")
        print(f"  Total statements: {len(statements)}")
        print(f"  Time: {segmentation_time:.2f}s")
        print(f"  Throughput: {statements_per_second:.1f} statements/sec")

    def test_benchmark_classification_performance(self, temp_db, large_hansard_text):
        """Benchmark statement classification performance."""
        mp_identifier = MPIdentifier(temp_db)
        segmenter = StatementSegmenter(mp_identifier)
        classifier = FillerDetector()

        # Segment first
        statements = segmenter.segment(large_hansard_text, session_id="test")

        # Benchmark classification
        start_time = time.time()
        classified = []
        for stmt in statements:
            stmt_type, confidence = classifier.classify(stmt)
            classified.append((stmt, stmt_type, confidence))
        classification_time = time.time() - start_time

        # Verify performance
        assert len(classified) == len(statements)
        assert classification_time < 2.0  # Should be very fast (rule-based)

        # Calculate throughput
        statements_per_second = len(classified) / classification_time
        assert statements_per_second > 50  # Should be very fast

        print("\nClassification Performance:")
        print(f"  Total statements: {len(classified)}")
        print(f"  Time: {classification_time:.2f}s")
        print(f"  Throughput: {statements_per_second:.1f} statements/sec")

    def test_benchmark_complete_hansard_processing(self, temp_db, large_hansard_text):
        """Benchmark complete Hansard processing pipeline."""
        mp_identifier = MPIdentifier(temp_db)
        segmenter = StatementSegmenter(mp_identifier)
        classifier = FillerDetector()

        # Benchmark complete pipeline
        start_time = time.time()

        # Segmentation
        statements = segmenter.segment(large_hansard_text, session_id="test")

        # Classification
        substantive = [stmt for stmt in statements if classifier.is_substantive(stmt)]

        processing_time = time.time() - start_time

        # Verify performance
        # For 100 statements, should complete in under 10 seconds
        assert processing_time < 10.0

        print("\nComplete Hansard Processing Performance:")
        print(f"  Total statements: {len(statements)}")
        print(f"  Substantive statements: {len(substantive)}")
        print(f"  Time: {processing_time:.2f}s")
        print(f"  Throughput: {len(statements)/processing_time:.1f} statements/sec")


class TestLLMAPIPerformance:
    """Test LLM API call performance."""

    @patch("anthropic.Anthropic")
    def test_benchmark_single_llm_call(self, mock_anthropic):
        """Benchmark single LLM API call."""
        # Setup mock
        mock_client = Mock()
        mock_anthropic.return_value = mock_client
        mock_response = Mock()
        mock_response.content = [
            Mock(
                text='{"sentiment": "positive", "sentiment_confidence": 0.9, "sentiment_explanation": "Supportive", "quality_score": 75, "quality_factors": {"clarity": 80}, "primary_topic": "Finance", "secondary_topics": [], "topic_confidence": 0.85, "key_points": ["Reform"], "citations": ["reform"]}'
            )
        ]
        mock_client.messages.create.return_value = mock_response

        llm_analyzer = LLMAnalyzer(api_key="test_key")
        llm_analyzer.client = mock_client

        stmt = Statement(
            text="This is a test statement about economic policy and reform.",
            mp_id=None,
            start_pos=0,
            end_pos=58,
        )

        # Benchmark
        start_time = time.time()
        analysis = llm_analyzer.analyze(stmt, context=None)
        call_time = time.time() - start_time

        # Verify
        assert analysis is not None
        # Mock call should be very fast
        assert call_time < 0.1

        print("\nLLM API Call Performance (mocked):")
        print(f"  Time: {call_time*1000:.1f}ms")

    @patch("anthropic.Anthropic")
    def test_benchmark_batch_llm_calls(self, mock_anthropic):
        """Benchmark batch LLM API calls."""
        # Setup mock
        mock_client = Mock()
        mock_anthropic.return_value = mock_client
        mock_response = Mock()
        mock_response.content = [
            Mock(
                text='{"sentiment": "positive", "sentiment_confidence": 0.9, "sentiment_explanation": "Supportive", "quality_score": 75, "quality_factors": {"clarity": 80}, "primary_topic": "Finance", "secondary_topics": [], "topic_confidence": 0.85, "key_points": ["Reform"], "citations": ["reform"]}'
            )
        ]
        mock_client.messages.create.return_value = mock_response

        llm_analyzer = LLMAnalyzer(api_key="test_key")
        llm_analyzer.client = mock_client

        # Create 10 statements
        statements = [
            Statement(
                text=f"Statement {i} about policy and reform.", mp_id=None, start_pos=0, end_pos=40
            )
            for i in range(10)
        ]

        # Benchmark batch processing
        start_time = time.time()
        analyses = []
        for stmt in statements:
            analysis = llm_analyzer.analyze(stmt, context=None)
            analyses.append(analysis)
        batch_time = time.time() - start_time

        # Verify
        assert len(analyses) == 10
        # Mock calls should be very fast
        assert batch_time < 1.0

        print("\nBatch LLM API Performance (mocked):")
        print(f"  Total statements: {len(statements)}")
        print(f"  Time: {batch_time:.2f}s")
        print(f"  Per statement: {batch_time/len(statements)*1000:.1f}ms")


class TestVectorDBPerformance:
    """Test vector database query performance."""

    def test_benchmark_vector_db_insertion(self, temp_vector_db):
        """Benchmark vector DB insertion performance."""
        from hansard_tales.config.settings import EmbeddingConfig
        from hansard_tales.vector_db import EmbeddingGenerator

        config = EmbeddingConfig(model_name="sentence-transformers/all-MiniLM-L6-v2")
        embedder = EmbeddingGenerator(config)

        # Generate embeddings for 100 statements
        texts = [f"Statement {i} about policy and reform." for i in range(100)]

        # Benchmark embedding generation
        start_time = time.time()
        embeddings = embedder.generate_batch(texts)
        embedding_time = time.time() - start_time

        # Benchmark insertion
        start_time = time.time()
        for i, (text, embedding) in enumerate(zip(texts, embeddings, strict=False)):
            temp_vector_db.insert(
                collection="statements",
                id=f"stmt_{i}",
                vector=embedding,
                payload={"index": i},
                text=text,
            )
        insertion_time = time.time() - start_time

        # Verify performance
        assert embedding_time < 10.0  # Should generate embeddings quickly
        assert insertion_time < 5.0  # Should insert quickly

        print("\nVector DB Insertion Performance:")
        print(f"  Embedding generation: {embedding_time:.2f}s")
        print(f"  Insertion time: {insertion_time:.2f}s")
        print(f"  Total: {embedding_time + insertion_time:.2f}s")
        print(f"  Throughput: {len(texts)/(embedding_time + insertion_time):.1f} docs/sec")

    def test_benchmark_vector_db_search(self, temp_vector_db):
        """Benchmark vector DB search performance."""
        from hansard_tales.config.settings import EmbeddingConfig
        from hansard_tales.vector_db import EmbeddingGenerator

        config = EmbeddingConfig(model_name="sentence-transformers/all-MiniLM-L6-v2")
        embedder = EmbeddingGenerator(config)

        # Insert 100 documents
        texts = [f"Statement {i} about policy and reform." for i in range(100)]
        embeddings = embedder.generate_batch(texts)

        for i, (text, embedding) in enumerate(zip(texts, embeddings, strict=False)):
            temp_vector_db.insert(
                collection="statements",
                id=f"stmt_{i}",
                vector=embedding,
                payload={"index": i},
                text=text,
            )

        # Benchmark search
        query = "policy reform"
        query_embedding = embedder.generate(query)

        start_time = time.time()
        results = temp_vector_db.search(
            collection="statements", query_vector=query_embedding, limit=10
        )
        search_time = time.time() - start_time

        # Verify performance
        assert len(results) > 0
        assert search_time < 0.5  # Should search very quickly

        print("\nVector DB Search Performance:")
        print(f"  Search time: {search_time*1000:.1f}ms")
        print(f"  Results: {len(results)}")

    def test_benchmark_context_retrieval(self, temp_db, temp_vector_db):
        """Benchmark complete context retrieval performance."""
        from hansard_tales.config.settings import EmbeddingConfig
        from hansard_tales.vector_db import EmbeddingGenerator

        config = EmbeddingConfig(model_name="sentence-transformers/all-MiniLM-L6-v2")
        embedder = EmbeddingGenerator(config)

        # Insert documents
        texts = [f"Statement {i} about policy and reform." for i in range(50)]
        embeddings = embedder.generate_batch(texts)

        for i, (text, embedding) in enumerate(zip(texts, embeddings, strict=False)):
            temp_vector_db.insert(
                collection="statements",
                id=f"stmt_{i}",
                vector=embedding,
                payload={"index": i},
                text=text,
            )

        # Benchmark context retrieval
        context_retriever = ContextRetriever(temp_vector_db, temp_db)

        stmt = Statement(
            text="We need comprehensive policy reform.", mp_id=None, start_pos=0, end_pos=37
        )

        start_time = time.time()
        context = context_retriever.retrieve(stmt, top_k=5)
        retrieval_time = time.time() - start_time

        # Verify performance
        assert context is not None
        assert retrieval_time < 1.0  # Should retrieve quickly

        print("\nContext Retrieval Performance:")
        print(f"  Time: {retrieval_time*1000:.1f}ms")


class TestSiteGenerationPerformance:
    """Test static site generation performance."""

    def test_benchmark_site_generation(self, temp_db, temp_output_dir):
        """Benchmark complete site generation."""
        # Add data
        session = temp_db.query(SessionORM).first()
        mps = temp_db.query(MPORM).all()

        # Add statements for each MP
        for mp in mps[:20]:  # Limit to 20 MPs for performance
            for i in range(5):
                stmt = StatementORM(
                    session_id=session.id,
                    mp_id=mp.id,
                    text=f"Statement {i} by {mp.name}",
                    statement_type="substantive",
                    start_pos=0,
                    end_pos=30,
                    sentiment="positive",
                    quality_score=75,
                    primary_topic="Finance",
                    created_at=datetime.now(UTC),
                    updated_at=datetime.now(UTC),
                )
                temp_db.add(stmt)
        temp_db.commit()

        # Benchmark site generation
        template_dir = Path("templates")
        site_generator = StaticSiteGenerator(temp_db, template_dir, temp_output_dir)

        start_time = time.time()
        site_generator._generate_homepage()
        site_generator._generate_mp_pages()
        site_generator._generate_session_pages()
        generation_time = time.time() - start_time

        # Verify performance
        # Should generate site quickly
        assert generation_time < 10.0

        # Verify output
        assert (temp_output_dir / "index.html").exists()
        assert (temp_output_dir / "mps" / "index.html").exists()

        print("\nSite Generation Performance:")
        print("  MPs: 20")
        print("  Statements: 100")
        print(f"  Time: {generation_time:.2f}s")


class TestBottleneckIdentification:
    """Test to identify performance bottlenecks."""

    @patch("anthropic.Anthropic")
    def test_identify_pipeline_bottlenecks(
        self, mock_anthropic, temp_db, temp_vector_db, large_hansard_text
    ):
        """Identify bottlenecks in the complete pipeline."""
        # Setup mocks
        mock_client = Mock()
        mock_anthropic.return_value = mock_client
        mock_response = Mock()
        mock_response.content = [
            Mock(
                text='{"sentiment": "positive", "sentiment_confidence": 0.9, "sentiment_explanation": "Supportive", "quality_score": 75, "quality_factors": {"clarity": 80}, "primary_topic": "Finance", "secondary_topics": [], "topic_confidence": 0.85, "key_points": ["Reform"], "citations": ["reform"]}'
            )
        ]
        mock_client.messages.create.return_value = mock_response

        # Initialize components
        mp_identifier = MPIdentifier(temp_db)
        segmenter = StatementSegmenter(mp_identifier)
        classifier = FillerDetector()
        context_retriever = ContextRetriever(temp_vector_db, temp_db)
        llm_analyzer = LLMAnalyzer(api_key="test_key")
        llm_analyzer.client = mock_client

        session = temp_db.query(SessionORM).first()

        # Measure each stage
        timings = {}

        # Stage 1: Segmentation
        start = time.time()
        statements = segmenter.segment(large_hansard_text, session_id=str(session.id))
        timings["segmentation"] = time.time() - start

        # Stage 2: Classification
        start = time.time()
        substantive = [stmt for stmt in statements if classifier.is_substantive(stmt)]
        timings["classification"] = time.time() - start

        # Stage 3: Context Retrieval (sample)
        start = time.time()
        for stmt in substantive[:10]:
            context_retriever.retrieve(stmt, top_k=3)
        timings["context_retrieval"] = time.time() - start

        # Stage 4: LLM Analysis (sample)
        start = time.time()
        for stmt in substantive[:10]:
            llm_analyzer.analyze(stmt, context=None)
        timings["llm_analysis"] = time.time() - start

        # Print bottleneck analysis
        print("\nPipeline Bottleneck Analysis:")
        print(f"  Statements processed: {len(statements)}")
        print(f"  Substantive: {len(substantive)}")
        print("\nStage Timings:")
        for stage, duration in sorted(timings.items(), key=lambda x: x[1], reverse=True):
            print(f"  {stage}: {duration:.3f}s")

        # Identify bottleneck
        bottleneck = max(timings.items(), key=lambda x: x[1])
        print(f"\nBottleneck: {bottleneck[0]} ({bottleneck[1]:.3f}s)")

        # Verify reasonable performance
        total_time = sum(timings.values())
        assert total_time < 15.0  # Total should be reasonable


class TestOptimizationOpportunities:
    """Test to identify optimization opportunities."""

    def test_caching_improves_performance(self, temp_db):
        """Test that caching improves MP identification performance."""
        mp_identifier = MPIdentifier(temp_db)

        # First lookup (cold cache)
        start = time.time()
        result1 = mp_identifier.identify("Hon. MP 0 (Constituency 0, UDA)")
        cold_time = time.time() - start

        # Second lookup (warm cache)
        start = time.time()
        result2 = mp_identifier.identify("Hon. MP 0 (Constituency 0, UDA)")
        warm_time = time.time() - start

        # Warm cache should be faster (or at least not slower)
        assert warm_time <= cold_time * 1.5  # Allow some variance

        print("\nCaching Performance:")
        print(f"  Cold cache: {cold_time*1000:.2f}ms")
        print(f"  Warm cache: {warm_time*1000:.2f}ms")
        print(f"  Speedup: {cold_time/warm_time:.1f}x")

    def test_batch_processing_improves_performance(self):
        """Test that batch processing is more efficient."""
        from hansard_tales.config.settings import EmbeddingConfig
        from hansard_tales.vector_db import EmbeddingGenerator

        config = EmbeddingConfig(model_name="sentence-transformers/all-MiniLM-L6-v2")
        embedder = EmbeddingGenerator(config)

        texts = [f"Statement {i}" for i in range(20)]

        # Individual processing
        start = time.time()
        for text in texts:
            embedder.generate(text)
        individual_time = time.time() - start

        # Batch processing
        start = time.time()
        embedder.generate_batch(texts)
        batch_time = time.time() - start

        # Batch should be faster
        assert batch_time < individual_time

        print("\nBatch Processing Performance:")
        print(f"  Individual: {individual_time:.2f}s")
        print(f"  Batch: {batch_time:.2f}s")
        print(f"  Speedup: {individual_time/batch_time:.1f}x")
