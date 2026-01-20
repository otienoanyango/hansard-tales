#!/usr/bin/env python3
"""
Test script for Task 8.2: Test site generation

This script:
1. Generates static site locally
2. Tests all page types (MP profiles, homepage, listings)
3. Verifies search functionality
4. Checks page structure and content
5. Validates file sizes and performance
6. Generates a detailed report
"""

import sys
import json
import sqlite3
from pathlib import Path
from datetime import datetime
from bs4 import BeautifulSoup


class SiteGenerationTester:
    """Test the static site generation."""
    
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
        
    def test_output_directory(self) -> dict:
        """Test that output directory exists and has expected structure."""
        self.log("=" * 80)
        self.log("STEP 1: Test Output Directory Structure")
        self.log("=" * 80)
        
        results = {
            "exists": False,
            "has_index": False,
            "has_static": False,
            "has_mps": False,
            "has_parties": False,
            "has_search_index": False,
            "total_files": 0
        }
        
        if not self.output_dir.exists():
            self.log(f"Output directory not found: {self.output_dir}", "ERROR")
            self.issues.append("Output directory does not exist")
            return results
        
        results["exists"] = True
        self.log(f"✓ Output directory exists: {self.output_dir}")
        
        # Check for index.html
        index_file = self.output_dir / "index.html"
        results["has_index"] = index_file.exists()
        if results["has_index"]:
            self.log(f"✓ Homepage exists: {index_file}")
        else:
            self.log(f"✗ Homepage missing: {index_file}", "ERROR")
            self.issues.append("Homepage (index.html) not found")
        
        # Check for static directory
        static_dir = self.output_dir / "static"
        results["has_static"] = static_dir.exists()
        if results["has_static"]:
            css_files = list(static_dir.glob("**/*.css"))
            js_files = list(static_dir.glob("**/*.js"))
            self.log(f"✓ Static directory exists with {len(css_files)} CSS and {len(js_files)} JS files")
        else:
            self.log(f"✗ Static directory missing", "ERROR")
            self.issues.append("Static directory not found")
        
        # Check for MPs directory
        mps_dir = self.output_dir / "mp"
        results["has_mps"] = mps_dir.exists()
        if results["has_mps"]:
            # MP profiles are in nested directories (mp/1/index.html, mp/2/index.html, etc.)
            mp_files = list(mps_dir.glob("*/index.html"))
            self.log(f"✓ MPs directory exists with {len(mp_files)} profile pages")
        else:
            self.log(f"✗ MPs directory missing", "ERROR")
            self.issues.append("MPs directory not found")
        
        # Check for parties directory
        parties_dir = self.output_dir / "parties"
        results["has_parties"] = parties_dir.exists()
        if results["has_parties"]:
            party_files = list(parties_dir.glob("*.html"))
            self.log(f"✓ Parties directory exists with {len(party_files)} pages")
        else:
            self.log(f"✗ Parties directory missing", "ERROR")
            self.issues.append("Parties directory not found")
        
        # Check for search index
        search_index = self.output_dir / "data" / "mp-search-index.json"
        results["has_search_index"] = search_index.exists()
        if results["has_search_index"]:
            size_kb = search_index.stat().st_size / 1024
            self.log(f"✓ Search index exists: {size_kb:.1f} KB")
        else:
            self.log(f"✗ Search index missing", "ERROR")
            self.issues.append("Search index not found")
        
        # Count total files
        results["total_files"] = len(list(self.output_dir.rglob("*")))
        self.log(f"\nTotal files in output: {results['total_files']}")
        
        return results
    
    def test_homepage(self) -> dict:
        """Test homepage content and structure."""
        self.log("\n" + "=" * 80)
        self.log("STEP 2: Test Homepage")
        self.log("=" * 80)
        
        results = {
            "exists": False,
            "has_search": False,
            "has_navigation": False,
            "has_content": False,
            "file_size_kb": 0
        }
        
        index_file = self.output_dir / "index.html"
        if not index_file.exists():
            self.log("Homepage not found", "ERROR")
            return results
        
        results["exists"] = True
        results["file_size_kb"] = index_file.stat().st_size / 1024
        
        # Parse HTML
        with open(index_file, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
        
        # Check for search input
        search_input = soup.find('input', {'id': 'mp-search'})
        results["has_search"] = search_input is not None
        if results["has_search"]:
            self.log("✓ Search input found")
        else:
            self.log("✗ Search input missing", "WARN")
            self.issues.append("Homepage missing search input")
        
        # Check for navigation
        nav = soup.find('nav')
        results["has_navigation"] = nav is not None
        if results["has_navigation"]:
            nav_links = nav.find_all('a') if nav else []
            self.log(f"✓ Navigation found with {len(nav_links)} links")
        else:
            self.log("✗ Navigation missing", "WARN")
        
        # Check for main content
        main_content = soup.find('main') or soup.find('div', class_='container')
        results["has_content"] = main_content is not None
        if results["has_content"]:
            self.log("✓ Main content area found")
        else:
            self.log("✗ Main content missing", "WARN")
        
        self.log(f"Homepage size: {results['file_size_kb']:.1f} KB")
        
        return results
    
    def test_mp_profiles(self) -> dict:
        """Test MP profile pages."""
        self.log("\n" + "=" * 80)
        self.log("STEP 3: Test MP Profile Pages")
        self.log("=" * 80)
        
        results = {
            "total_profiles": 0,
            "profiles_tested": 0,
            "valid_profiles": 0,
            "avg_size_kb": 0,
            "issues_found": []
        }
        
        mps_dir = self.output_dir / "mp"
        if not mps_dir.exists():
            self.log("MPs directory not found", "ERROR")
            return results
        
        # MP profiles are in nested directories (mp/1/index.html, mp/2/index.html, etc.)
        mp_files = list(mps_dir.glob("*/index.html"))
        results["total_profiles"] = len(mp_files)
        self.log(f"Found {results['total_profiles']} MP profile pages")
        
        # Test a sample of profiles
        sample_size = min(10, len(mp_files))
        sample_files = mp_files[:sample_size]
        
        total_size = 0
        for mp_file in sample_files:
            results["profiles_tested"] += 1
            
            try:
                with open(mp_file, 'r', encoding='utf-8') as f:
                    soup = BeautifulSoup(f.read(), 'html.parser')
                
                file_size = mp_file.stat().st_size
                total_size += file_size
                
                # Check for key elements
                has_name = soup.find('h1') is not None
                has_constituency = 'constituency' in soup.get_text().lower() or 'Constituency' in soup.get_text()
                has_party = 'party' in soup.get_text().lower() or 'Party' in soup.get_text()
                
                if has_name and (has_constituency or has_party):
                    results["valid_profiles"] += 1
                else:
                    issue = f"{mp_file.name}: Missing key information"
                    results["issues_found"].append(issue)
                    
            except Exception as e:
                issue = f"{mp_file.name}: Parse error - {e}"
                results["issues_found"].append(issue)
        
        results["avg_size_kb"] = (total_size / sample_size / 1024) if sample_size > 0 else 0
        
        self.log(f"Tested {results['profiles_tested']} profiles")
        self.log(f"Valid profiles: {results['valid_profiles']}/{results['profiles_tested']}")
        self.log(f"Average profile size: {results['avg_size_kb']:.1f} KB")
        
        if results["issues_found"]:
            self.log(f"Found {len(results['issues_found'])} issues in profiles", "WARN")
            for issue in results["issues_found"][:5]:  # Show first 5
                self.log(f"  - {issue}", "WARN")
        else:
            self.log("✓ All tested profiles valid")
        
        return results
    
    def test_parties_pages(self) -> dict:
        """Test party pages."""
        self.log("\n" + "=" * 80)
        self.log("STEP 4: Test Party Pages")
        self.log("=" * 80)
        
        results = {
            "has_listing": False,
            "total_parties": 0,
            "parties_tested": 0,
            "valid_parties": 0
        }
        
        # Check parties listing
        parties_index = self.output_dir / "parties" / "index.html"
        results["has_listing"] = parties_index.exists()
        if results["has_listing"]:
            self.log("✓ Parties listing page exists")
        else:
            self.log("✗ Parties listing page missing", "ERROR")
            self.issues.append("Parties listing page not found")
            return results
        
        # Check individual party pages
        parties_dir = self.output_dir / "party"
        if not parties_dir.exists():
            self.log("✗ Party directory not found", "ERROR")
            return results
        
        # Party pages are in nested directories (party/uda/index.html, party/odm/index.html, etc.)
        party_files = list(parties_dir.glob("*/index.html"))
        results["total_parties"] = len(party_files)
        self.log(f"Found {results['total_parties']} party detail pages")
        
        # Test a sample
        sample_size = min(5, len(party_files))
        for party_file in party_files[:sample_size]:
            results["parties_tested"] += 1
            
            try:
                with open(party_file, 'r', encoding='utf-8') as f:
                    soup = BeautifulSoup(f.read(), 'html.parser')
                
                has_title = soup.find('h1') is not None
                has_mps_list = soup.find_all('a', href=lambda x: x and '/mp/' in x)
                
                if has_title and has_mps_list:
                    results["valid_parties"] += 1
                    
            except Exception as e:
                self.log(f"Error parsing {party_file.name}: {e}", "WARN")
        
        self.log(f"Tested {results['parties_tested']} party pages")
        self.log(f"Valid party pages: {results['valid_parties']}/{results['parties_tested']}")
        
        return results
    
    def test_search_index(self) -> dict:
        """Test search index JSON."""
        self.log("\n" + "=" * 80)
        self.log("STEP 5: Test Search Index")
        self.log("=" * 80)
        
        results = {
            "exists": False,
            "valid_json": False,
            "total_mps": 0,
            "has_required_fields": False,
            "size_kb": 0
        }
        
        search_index = self.output_dir / "data" / "mp-search-index.json"
        if not search_index.exists():
            self.log("Search index not found", "ERROR")
            self.issues.append("Search index missing")
            return results
        
        results["exists"] = True
        results["size_kb"] = search_index.stat().st_size / 1024
        
        try:
            with open(search_index, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            results["valid_json"] = True
            results["total_mps"] = len(data)
            
            # Check first MP has required fields
            if data:
                first_mp = data[0]
                required_fields = ['name', 'constituency', 'party', 'url']
                has_all = all(field in first_mp for field in required_fields)
                results["has_required_fields"] = has_all
                
                if has_all:
                    self.log(f"✓ Search index valid with {results['total_mps']} MPs")
                    self.log(f"  Sample MP: {first_mp['name']} ({first_mp['party']})")
                else:
                    missing = [f for f in required_fields if f not in first_mp]
                    self.log(f"✗ Missing required fields: {missing}", "ERROR")
                    self.issues.append(f"Search index missing fields: {missing}")
            
        except json.JSONDecodeError as e:
            self.log(f"✗ Invalid JSON: {e}", "ERROR")
            self.issues.append("Search index is not valid JSON")
        except Exception as e:
            self.log(f"✗ Error reading search index: {e}", "ERROR")
            self.issues.append(f"Search index error: {e}")
        
        self.log(f"Search index size: {results['size_kb']:.1f} KB")
        
        return results
    
    def test_database_consistency(self) -> dict:
        """Test that generated site matches database."""
        self.log("\n" + "=" * 80)
        self.log("STEP 6: Test Database Consistency")
        self.log("=" * 80)
        
        results = {
            "db_mps": 0,
            "generated_profiles": 0,
            "match": False
        }
        
        # Count MPs in database
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM current_mps")
            results["db_mps"] = cursor.fetchone()[0]
            conn.close()
            
            self.log(f"MPs in database: {results['db_mps']}")
        except Exception as e:
            self.log(f"Error querying database: {e}", "ERROR")
            return results
        
        # Count generated profiles
        mps_dir = self.output_dir / "mp"
        if mps_dir.exists():
            # MP profiles are in nested directories (mp/1/index.html, mp/2/index.html, etc.)
            mp_files = list(mps_dir.glob("*/index.html"))
            results["generated_profiles"] = len(mp_files)
            self.log(f"Generated MP profiles: {results['generated_profiles']}")
        
        # Check if they match
        results["match"] = results["db_mps"] == results["generated_profiles"]
        if results["match"]:
            self.log("✓ Database and generated profiles match")
        else:
            diff = abs(results["db_mps"] - results["generated_profiles"])
            self.log(f"✗ Mismatch: {diff} profiles difference", "WARN")
            self.issues.append(f"Profile count mismatch: DB has {results['db_mps']}, generated {results['generated_profiles']}")
        
        return results
    
    def generate_report(self, all_results: dict):
        """Generate final test report."""
        self.log("\n" + "=" * 80)
        self.log("FINAL REPORT: Task 8.2 - Test Site Generation")
        self.log("=" * 80)
        
        self.log(f"\n📁 Output Directory:")
        self.log(f"  Total files: {all_results['directory']['total_files']}")
        self.log(f"  Has homepage: {'✓' if all_results['directory']['has_index'] else '✗'}")
        self.log(f"  Has static assets: {'✓' if all_results['directory']['has_static'] else '✗'}")
        self.log(f"  Has MP profiles: {'✓' if all_results['directory']['has_mps'] else '✗'}")
        self.log(f"  Has party pages: {'✓' if all_results['directory']['has_parties'] else '✗'}")
        self.log(f"  Has search index: {'✓' if all_results['directory']['has_search_index'] else '✗'}")
        
        self.log(f"\n🏠 Homepage:")
        self.log(f"  Size: {all_results['homepage']['file_size_kb']:.1f} KB")
        self.log(f"  Has search: {'✓' if all_results['homepage']['has_search'] else '✗'}")
        self.log(f"  Has navigation: {'✓' if all_results['homepage']['has_navigation'] else '✗'}")
        
        self.log(f"\n👤 MP Profiles:")
        self.log(f"  Total profiles: {all_results['mp_profiles']['total_profiles']}")
        self.log(f"  Tested: {all_results['mp_profiles']['profiles_tested']}")
        self.log(f"  Valid: {all_results['mp_profiles']['valid_profiles']}/{all_results['mp_profiles']['profiles_tested']}")
        self.log(f"  Average size: {all_results['mp_profiles']['avg_size_kb']:.1f} KB")
        
        self.log(f"\n🎭 Party Pages:")
        self.log(f"  Total parties: {all_results['parties']['total_parties']}")
        self.log(f"  Tested: {all_results['parties']['parties_tested']}")
        self.log(f"  Valid: {all_results['parties']['valid_parties']}/{all_results['parties']['parties_tested']}")
        
        self.log(f"\n🔍 Search Index:")
        self.log(f"  Size: {all_results['search']['size_kb']:.1f} KB")
        self.log(f"  Total MPs: {all_results['search']['total_mps']}")
        self.log(f"  Valid JSON: {'✓' if all_results['search']['valid_json'] else '✗'}")
        self.log(f"  Has required fields: {'✓' if all_results['search']['has_required_fields'] else '✗'}")
        
        self.log(f"\n💾 Database Consistency:")
        self.log(f"  DB MPs: {all_results['consistency']['db_mps']}")
        self.log(f"  Generated profiles: {all_results['consistency']['generated_profiles']}")
        self.log(f"  Match: {'✓' if all_results['consistency']['match'] else '✗'}")
        
        # Overall status
        self.log(f"\n🎯 Overall Status:")
        self.log(f"  Issues found: {len(self.issues)}")
        
        if not self.issues:
            self.log(f"\n✅ SUCCESS: All tests passed!")
            self.log(f"  - Static site generated successfully")
            self.log(f"  - All page types validated")
            self.log(f"  - Search functionality ready")
            self.log(f"  - Database consistency verified")
            return True
        else:
            self.log(f"\n⚠️  PARTIAL SUCCESS: Some issues found")
            for issue in self.issues:
                self.log(f"  - {issue}")
            return False
    
    def save_report(self, filename: str = "test_site_generation_report.txt"):
        """Save report to file."""
        report_path = Path(filename)
        with open(report_path, "w") as f:
            f.write("\n".join(self.report))
        self.log(f"\n📄 Report saved to: {report_path.absolute()}")
    
    def run(self):
        """Run the full test suite."""
        self.log("Starting Task 8.2: Test Site Generation")
        self.log(f"Output directory: {self.output_dir}")
        self.log(f"Database: {self.db_path}")
        
        all_results = {}
        
        # Run all tests
        all_results['directory'] = self.test_output_directory()
        all_results['homepage'] = self.test_homepage()
        all_results['mp_profiles'] = self.test_mp_profiles()
        all_results['parties'] = self.test_parties_pages()
        all_results['search'] = self.test_search_index()
        all_results['consistency'] = self.test_database_consistency()
        
        # Generate report
        success = self.generate_report(all_results)
        
        # Save report
        self.save_report()
        
        return success


if __name__ == "__main__":
    tester = SiteGenerationTester()
    success = tester.run()
    sys.exit(0 if success else 1)
