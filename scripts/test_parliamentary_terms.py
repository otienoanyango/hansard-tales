#!/usr/bin/env python3
"""
Test script for Task 8.3: Test parliamentary term tracking

This script:
1. Verifies current term data displays correctly
2. Tests historical term display (if data available)
3. Tests term filtering on MP profiles
4. Verifies search index includes term data
5. Generates a detailed report
"""

import sys
import json
import sqlite3
from pathlib import Path
from datetime import datetime
from bs4 import BeautifulSoup


class ParliamentaryTermTester:
    """Test parliamentary term tracking functionality."""
    
    def __init__(self, output_dir: str = "output", db_path: str = "data/hansard.db"):
        self.output_dir = Path(output_dir)
        self.db_path = db_path
        self.report = []
        self.issues = []
        
    def log(self, message: str, level: str = "INFO"):
        """Log a message to console and report."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted = f"[{timestamp}] {level}: {message}"
        print(formatted)
        self.report.append(formatted)
        
    def test_database_terms(self) -> dict:
        """Test parliamentary terms in database."""
        self.log("=" * 80)
        self.log("STEP 1: Test Database Parliamentary Terms")
        self.log("=" * 80)
        
        results = {
            "total_terms": 0,
            "current_term": None,
            "has_13th_parliament": False,
            "has_12th_parliament": False,
            "mps_with_multiple_terms": 0
        }
        
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            
            # Get all parliamentary terms
            terms = conn.execute('''
                SELECT id, term_number, start_date, end_date, is_current
                FROM parliamentary_terms
                ORDER BY term_number DESC
            ''').fetchall()
            
            results["total_terms"] = len(terms)
            self.log(f"Found {results['total_terms']} parliamentary terms in database")
            
            for term in terms:
                self.log(f"  Term {term['term_number']}: {term['start_date']} to {term['end_date']} "
                        f"{'(CURRENT)' if term['is_current'] else ''}")
                
                if term['is_current']:
                    results["current_term"] = term['term_number']
                
                if term['term_number'] == 13:
                    results["has_13th_parliament"] = True
                elif term['term_number'] == 12:
                    results["has_12th_parliament"] = True
            
            # Check for MPs with multiple terms
            mps_multi_terms = conn.execute('''
                SELECT mp_id, COUNT(*) as term_count
                FROM mp_terms
                GROUP BY mp_id
                HAVING term_count > 1
            ''').fetchall()
            
            results["mps_with_multiple_terms"] = len(mps_multi_terms)
            
            if results["mps_with_multiple_terms"] > 0:
                self.log(f"\n✓ Found {results['mps_with_multiple_terms']} MPs with multiple terms")
            else:
                self.log(f"\n⚠ No MPs with multiple terms found", "WARN")
            
            conn.close()
            
            # Validation
            if results["current_term"] is None:
                self.log("✗ No current term marked in database", "ERROR")
                self.issues.append("No current parliamentary term marked")
            else:
                self.log(f"✓ Current term: {results['current_term']}")
            
            if not results["has_13th_parliament"]:
                self.log("✗ 13th Parliament not found in database", "ERROR")
                self.issues.append("13th Parliament missing from database")
            else:
                self.log("✓ 13th Parliament present")
            
        except Exception as e:
            self.log(f"✗ Database error: {e}", "ERROR")
            self.issues.append(f"Database error: {e}")
        
        return results
    
    def test_mp_profile_terms(self) -> dict:
        """Test term display on MP profile pages."""
        self.log("\n" + "=" * 80)
        self.log("STEP 2: Test MP Profile Term Display")
        self.log("=" * 80)
        
        results = {
            "profiles_tested": 0,
            "profiles_with_current_term": 0,
            "profiles_with_historical_terms": 0,
            "profiles_with_term_filter": 0,
            "issues_found": []
        }
        
        mps_dir = self.output_dir / "mp"
        if not mps_dir.exists():
            self.log("MPs directory not found", "ERROR")
            self.issues.append("MPs directory not found")
            return results
        
        # Test a sample of profiles
        mp_files = list(mps_dir.glob("*/index.html"))
        sample_size = min(20, len(mp_files))
        
        self.log(f"Testing {sample_size} MP profiles for term data...")
        
        for mp_file in mp_files[:sample_size]:
            results["profiles_tested"] += 1
            
            try:
                with open(mp_file, 'r', encoding='utf-8') as f:
                    soup = BeautifulSoup(f.read(), 'html.parser')
                
                text = soup.get_text().lower()
                
                # Check for current term information
                has_current_term = (
                    'current term' in text or
                    'term 13' in text or
                    '13th parliament' in text
                )
                
                if has_current_term:
                    results["profiles_with_current_term"] += 1
                
                # Check for historical terms section
                has_historical = (
                    'historical' in text or
                    'previous term' in text or
                    'term 12' in text
                )
                
                if has_historical:
                    results["profiles_with_historical_terms"] += 1
                
                # Check for term filter (if implemented)
                has_filter = soup.find('select') is not None or 'filter' in text
                
                if has_filter:
                    results["profiles_with_term_filter"] += 1
                
            except Exception as e:
                issue = f"{mp_file.name}: Parse error - {e}"
                results["issues_found"].append(issue)
        
        # Report results
        self.log(f"\nTested {results['profiles_tested']} profiles:")
        self.log(f"  Profiles with current term info: {results['profiles_with_current_term']}/{results['profiles_tested']}")
        self.log(f"  Profiles with historical terms: {results['profiles_with_historical_terms']}/{results['profiles_tested']}")
        self.log(f"  Profiles with term filter: {results['profiles_with_term_filter']}/{results['profiles_tested']}")
        
        # Validation
        if results["profiles_with_current_term"] == 0:
            self.log("✗ No profiles display current term information", "ERROR")
            self.issues.append("MP profiles missing current term information")
        elif results["profiles_with_current_term"] < results["profiles_tested"]:
            self.log(f"⚠ Only {results['profiles_with_current_term']}/{results['profiles_tested']} profiles show current term", "WARN")
        else:
            self.log("✓ All tested profiles display current term information")
        
        if results["profiles_with_historical_terms"] > 0:
            self.log(f"✓ {results['profiles_with_historical_terms']} profiles display historical terms")
        else:
            self.log("⚠ No profiles display historical terms (may be expected if no MPs have multiple terms)", "WARN")
        
        return results
    
    def test_search_index_terms(self) -> dict:
        """Test term data in search index."""
        self.log("\n" + "=" * 80)
        self.log("STEP 3: Test Search Index Term Data")
        self.log("=" * 80)
        
        results = {
            "has_search_index": False,
            "total_mps": 0,
            "mps_with_current_term": 0,
            "mps_with_historical_terms": 0,
            "sample_mp": None
        }
        
        search_index = self.output_dir / "data" / "mp-search-index.json"
        if not search_index.exists():
            self.log("Search index not found", "ERROR")
            self.issues.append("Search index not found")
            return results
        
        results["has_search_index"] = True
        
        try:
            with open(search_index, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            results["total_mps"] = len(data)
            self.log(f"Search index contains {results['total_mps']} MPs")
            
            # Check term data in each MP entry
            for mp in data:
                # Check for current_term field
                if 'current_term' in mp:
                    results["mps_with_current_term"] += 1
                
                # Check for historical_terms field
                if 'historical_terms' in mp and len(mp['historical_terms']) > 0:
                    results["mps_with_historical_terms"] += 1
            
            # Get a sample MP with historical terms
            for mp in data:
                if 'historical_terms' in mp and len(mp['historical_terms']) > 1:
                    results["sample_mp"] = mp
                    break
            
            # Report results
            self.log(f"\nSearch index term data:")
            self.log(f"  MPs with current_term field: {results['mps_with_current_term']}/{results['total_mps']}")
            self.log(f"  MPs with historical_terms: {results['mps_with_historical_terms']}/{results['total_mps']}")
            
            if results["sample_mp"]:
                self.log(f"\nSample MP with multiple terms:")
                self.log(f"  Name: {results['sample_mp']['name']}")
                self.log(f"  Current term: {results['sample_mp']['current_term']['term_number']}")
                self.log(f"  Historical terms: {len(results['sample_mp']['historical_terms'])} terms")
                for term in results['sample_mp']['historical_terms']:
                    self.log(f"    - Term {term['term_number']}: {term['constituency']} ({term['party']})")
            
            # Validation
            if results["mps_with_current_term"] == results["total_mps"]:
                self.log("\n✓ All MPs have current_term data in search index")
            else:
                missing = results["total_mps"] - results["mps_with_current_term"]
                self.log(f"\n✗ {missing} MPs missing current_term data", "ERROR")
                self.issues.append(f"{missing} MPs missing current_term in search index")
            
            if results["mps_with_historical_terms"] > 0:
                self.log(f"✓ {results['mps_with_historical_terms']} MPs have historical_terms data")
            else:
                self.log("⚠ No MPs have historical_terms data (may be expected)", "WARN")
            
        except json.JSONDecodeError as e:
            self.log(f"✗ Invalid JSON: {e}", "ERROR")
            self.issues.append("Search index is not valid JSON")
        except Exception as e:
            self.log(f"✗ Error reading search index: {e}", "ERROR")
            self.issues.append(f"Search index error: {e}")
        
        return results
    
    def test_term_performance_data(self) -> dict:
        """Test term-specific performance data."""
        self.log("\n" + "=" * 80)
        self.log("STEP 4: Test Term-Specific Performance Data")
        self.log("=" * 80)
        
        results = {
            "mps_with_statements": 0,
            "statements_by_term": {},
            "sample_mp_performance": None
        }
        
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            
            # Get statements by term
            term_stats = conn.execute('''
                SELECT 
                    pt.term_number,
                    COUNT(DISTINCT s.id) as statement_count,
                    COUNT(DISTINCT s.mp_id) as mp_count
                FROM parliamentary_terms pt
                LEFT JOIN hansard_sessions hs ON hs.term_id = pt.id
                LEFT JOIN statements s ON s.session_id = hs.id
                GROUP BY pt.term_number
                ORDER BY pt.term_number DESC
            ''').fetchall()
            
            self.log("Statements by parliamentary term:")
            for stat in term_stats:
                results["statements_by_term"][stat['term_number']] = {
                    'statements': stat['statement_count'],
                    'mps': stat['mp_count']
                }
                self.log(f"  Term {stat['term_number']}: {stat['statement_count']} statements from {stat['mp_count']} MPs")
            
            # Get sample MP with performance data
            sample_mp = conn.execute('''
                SELECT 
                    m.name,
                    pt.term_number,
                    COUNT(DISTINCT s.id) as statement_count
                FROM mps m
                JOIN mp_terms mt ON m.id = mt.mp_id
                JOIN parliamentary_terms pt ON mt.term_id = pt.id
                LEFT JOIN hansard_sessions hs ON hs.term_id = pt.id
                LEFT JOIN statements s ON s.mp_id = m.id AND s.session_id = hs.id
                WHERE s.id IS NOT NULL
                GROUP BY m.id, pt.term_number
                HAVING statement_count > 0
                LIMIT 1
            ''').fetchone()
            
            if sample_mp:
                results["sample_mp_performance"] = {
                    'name': sample_mp['name'],
                    'term': sample_mp['term_number'],
                    'statements': sample_mp['statement_count']
                }
                self.log(f"\nSample MP performance:")
                self.log(f"  {sample_mp['name']}: {sample_mp['statement_count']} statements in Term {sample_mp['term_number']}")
            
            conn.close()
            
            # Validation
            total_statements = sum(term['statements'] for term in results["statements_by_term"].values())
            if total_statements > 0:
                self.log(f"\n✓ Found {total_statements} total statements across all terms")
            else:
                self.log("\n⚠ No statements found in database", "WARN")
            
        except Exception as e:
            self.log(f"✗ Database error: {e}", "ERROR")
            self.issues.append(f"Performance data error: {e}")
        
        return results
    
    def generate_report(self, all_results: dict):
        """Generate final test report."""
        self.log("\n" + "=" * 80)
        self.log("FINAL REPORT: Task 8.3 - Test Parliamentary Term Tracking")
        self.log("=" * 80)
        
        self.log(f"\n📊 Database Terms:")
        self.log(f"  Total terms: {all_results['database']['total_terms']}")
        self.log(f"  Current term: {all_results['database']['current_term']}")
        self.log(f"  Has 13th Parliament: {'✓' if all_results['database']['has_13th_parliament'] else '✗'}")
        self.log(f"  Has 12th Parliament: {'✓' if all_results['database']['has_12th_parliament'] else '✗'}")
        self.log(f"  MPs with multiple terms: {all_results['database']['mps_with_multiple_terms']}")
        
        self.log(f"\n👤 MP Profile Pages:")
        self.log(f"  Profiles tested: {all_results['profiles']['profiles_tested']}")
        self.log(f"  With current term: {all_results['profiles']['profiles_with_current_term']}/{all_results['profiles']['profiles_tested']}")
        self.log(f"  With historical terms: {all_results['profiles']['profiles_with_historical_terms']}/{all_results['profiles']['profiles_tested']}")
        self.log(f"  With term filter: {all_results['profiles']['profiles_with_term_filter']}/{all_results['profiles']['profiles_tested']}")
        
        self.log(f"\n🔍 Search Index:")
        self.log(f"  Total MPs: {all_results['search']['total_mps']}")
        self.log(f"  With current_term: {all_results['search']['mps_with_current_term']}/{all_results['search']['total_mps']}")
        self.log(f"  With historical_terms: {all_results['search']['mps_with_historical_terms']}/{all_results['search']['total_mps']}")
        
        self.log(f"\n📈 Performance Data:")
        for term_num, stats in all_results['performance']['statements_by_term'].items():
            self.log(f"  Term {term_num}: {stats['statements']} statements from {stats['mps']} MPs")
        
        # Overall status
        self.log(f"\n🎯 Overall Status:")
        self.log(f"  Issues found: {len(self.issues)}")
        
        if not self.issues:
            self.log(f"\n✅ SUCCESS: All parliamentary term tracking tests passed!")
            self.log(f"  - Database terms configured correctly")
            self.log(f"  - MP profiles display term information")
            self.log(f"  - Search index includes term data")
            self.log(f"  - Performance data tracked by term")
            return True
        else:
            self.log(f"\n⚠️  PARTIAL SUCCESS: Some issues found")
            for issue in self.issues:
                self.log(f"  - {issue}")
            return False
    
    def save_report(self, filename: str = "test_parliamentary_terms_report.txt"):
        """Save report to file."""
        report_path = Path(filename)
        with open(report_path, "w") as f:
            f.write("\n".join(self.report))
        self.log(f"\n📄 Report saved to: {report_path.absolute()}")
    
    def run(self):
        """Run the full test suite."""
        self.log("Starting Task 8.3: Test Parliamentary Term Tracking")
        self.log(f"Output directory: {self.output_dir}")
        self.log(f"Database: {self.db_path}")
        
        all_results = {}
        
        # Run all tests
        all_results['database'] = self.test_database_terms()
        all_results['profiles'] = self.test_mp_profile_terms()
        all_results['search'] = self.test_search_index_terms()
        all_results['performance'] = self.test_term_performance_data()
        
        # Generate report
        success = self.generate_report(all_results)
        
        # Save report
        self.save_report()
        
        return success


if __name__ == "__main__":
    tester = ParliamentaryTermTester()
    success = tester.run()
    sys.exit(0 if success else 1)
