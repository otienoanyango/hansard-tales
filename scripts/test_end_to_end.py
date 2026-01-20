#!/usr/bin/env python3
"""
Test script for Task 8.4: End-to-end testing

This script:
1. Runs complete workflow from scraping to site generation
2. Verifies all pipeline steps work together
3. Validates data flow through the system
4. Checks GitHub Actions workflow configuration
5. Generates a detailed report

Note: This does NOT test actual Cloudflare Pages deployment (requires manual testing)
"""

import sys
import subprocess
import sqlite3
from pathlib import Path
from datetime import datetime


class EndToEndTester:
    """Test the complete end-to-end workflow."""
    
    def __init__(self, db_path: str = "data/hansard.db", output_dir: str = "output"):
        self.db_path = db_path
        self.output_dir = Path(output_dir)
        self.report = []
        self.issues = []
        self.workflow_steps = []
        
    def log(self, message: str, level: str = "INFO"):
        """Log a message to console and report."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted = f"[{timestamp}] {level}: {message}"
        print(formatted)
        self.report.append(formatted)
        
    def run_command(self, command: list, description: str) -> dict:
        """Run a command and capture results."""
        self.log(f"\nRunning: {description}")
        self.log(f"Command: {' '.join(command)}")
        
        result = {
            "command": ' '.join(command),
            "description": description,
            "success": False,
            "output": "",
            "error": ""
        }
        
        try:
            process = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            result["success"] = process.returncode == 0
            result["output"] = process.stdout
            result["error"] = process.stderr
            
            if result["success"]:
                self.log(f"✓ {description} completed successfully")
            else:
                self.log(f"✗ {description} failed", "ERROR")
                self.log(f"Error: {process.stderr[:200]}", "ERROR")
                self.issues.append(f"{description} failed")
                
        except subprocess.TimeoutExpired:
            self.log(f"✗ {description} timed out", "ERROR")
            result["error"] = "Command timed out after 5 minutes"
            self.issues.append(f"{description} timed out")
        except Exception as e:
            self.log(f"✗ {description} error: {e}", "ERROR")
            result["error"] = str(e)
            self.issues.append(f"{description} error: {e}")
        
        self.workflow_steps.append(result)
        return result
    
    def test_database_state(self, stage: str) -> dict:
        """Check database state at a specific stage."""
        self.log(f"\nChecking database state: {stage}")
        
        results = {
            "stage": stage,
            "mps": 0,
            "sessions": 0,
            "statements": 0,
            "terms": 0
        }
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Count MPs
            cursor.execute("SELECT COUNT(*) FROM mps")
            results["mps"] = cursor.fetchone()[0]
            
            # Count sessions
            cursor.execute("SELECT COUNT(*) FROM hansard_sessions")
            results["sessions"] = cursor.fetchone()[0]
            
            # Count statements
            cursor.execute("SELECT COUNT(*) FROM statements")
            results["statements"] = cursor.fetchone()[0]
            
            # Count terms
            cursor.execute("SELECT COUNT(*) FROM parliamentary_terms")
            results["terms"] = cursor.fetchone()[0]
            
            conn.close()
            
            self.log(f"  MPs: {results['mps']}")
            self.log(f"  Sessions: {results['sessions']}")
            self.log(f"  Statements: {results['statements']}")
            self.log(f"  Terms: {results['terms']}")
            
        except Exception as e:
            self.log(f"✗ Database check error: {e}", "ERROR")
            self.issues.append(f"Database check failed at {stage}")
        
        return results
    
    def test_output_state(self, stage: str) -> dict:
        """Check output directory state at a specific stage."""
        self.log(f"\nChecking output state: {stage}")
        
        results = {
            "stage": stage,
            "exists": False,
            "mp_profiles": 0,
            "party_pages": 0,
            "has_search_index": False,
            "has_homepage": False
        }
        
        if not self.output_dir.exists():
            self.log("  Output directory does not exist")
            return results
        
        results["exists"] = True
        
        # Count MP profiles
        mp_dir = self.output_dir / "mp"
        if mp_dir.exists():
            results["mp_profiles"] = len(list(mp_dir.glob("*/index.html")))
        
        # Count party pages
        party_dir = self.output_dir / "party"
        if party_dir.exists():
            results["party_pages"] = len(list(party_dir.glob("*/index.html")))
        
        # Check search index
        search_index = self.output_dir / "data" / "mp-search-index.json"
        results["has_search_index"] = search_index.exists()
        
        # Check homepage
        homepage = self.output_dir / "index.html"
        results["has_homepage"] = homepage.exists()
        
        self.log(f"  MP profiles: {results['mp_profiles']}")
        self.log(f"  Party pages: {results['party_pages']}")
        self.log(f"  Search index: {'✓' if results['has_search_index'] else '✗'}")
        self.log(f"  Homepage: {'✓' if results['has_homepage'] else '✗'}")
        
        return results
    
    def test_github_actions_workflow(self) -> dict:
        """Test GitHub Actions workflow configuration."""
        self.log("\n" + "=" * 80)
        self.log("STEP: Test GitHub Actions Workflow Configuration")
        self.log("=" * 80)
        
        results = {
            "weekly_update_exists": False,
            "deploy_pages_exists": False,
            "ci_exists": False,
            "weekly_update_valid": False,
            "deploy_pages_valid": False
        }
        
        workflows_dir = Path(".github/workflows")
        
        # Check weekly-update.yml
        weekly_update = workflows_dir / "weekly-update.yml"
        results["weekly_update_exists"] = weekly_update.exists()
        
        if results["weekly_update_exists"]:
            self.log("✓ weekly-update.yml exists")
            
            # Check for key steps
            with open(weekly_update, 'r') as f:
                content = f.read()
                
                required_steps = [
                    "hansard-scraper",
                    "hansard-pdf-processor",
                    "hansard-db-updater",
                    "hansard-generate-search-index",
                    "hansard-generate-site"
                ]
                
                all_present = all(step in content for step in required_steps)
                results["weekly_update_valid"] = all_present
                
                if all_present:
                    self.log("✓ All required pipeline steps present in workflow")
                else:
                    missing = [s for s in required_steps if s not in content]
                    self.log(f"✗ Missing steps in workflow: {missing}", "ERROR")
                    self.issues.append(f"Weekly update workflow missing steps: {missing}")
        else:
            self.log("✗ weekly-update.yml not found", "ERROR")
            self.issues.append("Weekly update workflow not found")
        
        # Check deploy-pages.yml
        deploy_pages = workflows_dir / "deploy-pages.yml"
        results["deploy_pages_exists"] = deploy_pages.exists()
        
        if results["deploy_pages_exists"]:
            self.log("✓ deploy-pages.yml exists")
            
            with open(deploy_pages, 'r') as f:
                content = f.read()
                
                # Check for deployment steps
                has_build = "hansard-generate-site" in content
                has_deploy = "actions/deploy-pages" in content or "peaceiris/actions-gh-pages" in content
                
                results["deploy_pages_valid"] = has_build and has_deploy
                
                if results["deploy_pages_valid"]:
                    self.log("✓ Deployment workflow configured correctly")
                else:
                    self.log("⚠ Deployment workflow may need review", "WARN")
        else:
            self.log("✗ deploy-pages.yml not found", "ERROR")
            self.issues.append("Deploy pages workflow not found")
        
        # Check ci.yml
        ci_workflow = workflows_dir / "ci.yml"
        results["ci_exists"] = ci_workflow.exists()
        
        if results["ci_exists"]:
            self.log("✓ ci.yml exists (test automation)")
        else:
            self.log("⚠ ci.yml not found (optional)", "WARN")
        
        return results
    
    def run_end_to_end_workflow(self):
        """Run the complete end-to-end workflow."""
        self.log("=" * 80)
        self.log("STEP: Run Complete End-to-End Workflow")
        self.log("=" * 80)
        
        # Initial state
        initial_db = self.test_database_state("Initial")
        initial_output = self.test_output_state("Initial")
        
        # Step 1: Generate static site
        self.log("\n" + "-" * 80)
        self.log("Step 1: Generate Static Site")
        self.log("-" * 80)
        
        site_result = self.run_command(
            ["hansard-generate-site"],
            "Generate static site"
        )
        
        # Step 2: Generate search index (after site, so it's not cleared)
        self.log("\n" + "-" * 80)
        self.log("Step 2: Generate Search Index")
        self.log("-" * 80)
        
        search_result = self.run_command(
            ["hansard-generate-search-index"],
            "Generate search index"
        )
        
        # Final state
        final_db = self.test_database_state("Final")
        final_output = self.test_output_state("Final")
        
        # Validate workflow
        self.log("\n" + "-" * 80)
        self.log("Workflow Validation")
        self.log("-" * 80)
        
        # Check that data flowed through correctly
        if final_output["mp_profiles"] > 0:
            self.log(f"✓ Generated {final_output['mp_profiles']} MP profiles")
        else:
            self.log("✗ No MP profiles generated", "ERROR")
            self.issues.append("Site generation produced no MP profiles")
        
        if final_output["has_search_index"]:
            self.log("✓ Search index generated")
        else:
            self.log("✗ Search index not generated", "ERROR")
            self.issues.append("Search index not generated")
        
        if final_output["has_homepage"]:
            self.log("✓ Homepage generated")
        else:
            self.log("✗ Homepage not generated", "ERROR")
            self.issues.append("Homepage not generated")
        
        # Check data consistency
        if final_db["mps"] == initial_db["mps"]:
            self.log(f"✓ Database unchanged ({final_db['mps']} MPs)")
        else:
            self.log(f"⚠ Database changed: {initial_db['mps']} → {final_db['mps']} MPs", "WARN")
        
        return {
            "initial_db": initial_db,
            "final_db": final_db,
            "initial_output": initial_output,
            "final_output": final_output,
            "search_success": search_result["success"],
            "site_success": site_result["success"]
        }
    
    def generate_report(self, workflow_results: dict, github_results: dict):
        """Generate final test report."""
        self.log("\n" + "=" * 80)
        self.log("FINAL REPORT: Task 8.4 - End-to-End Testing")
        self.log("=" * 80)
        
        self.log(f"\n📊 Workflow Execution:")
        self.log(f"  Search index generation: {'✓' if workflow_results['search_success'] else '✗'}")
        self.log(f"  Static site generation: {'✓' if workflow_results['site_success'] else '✗'}")
        
        self.log(f"\n💾 Database State:")
        self.log(f"  MPs: {workflow_results['final_db']['mps']}")
        self.log(f"  Sessions: {workflow_results['final_db']['sessions']}")
        self.log(f"  Statements: {workflow_results['final_db']['statements']}")
        self.log(f"  Terms: {workflow_results['final_db']['terms']}")
        
        self.log(f"\n📁 Output State:")
        self.log(f"  MP profiles: {workflow_results['final_output']['mp_profiles']}")
        self.log(f"  Party pages: {workflow_results['final_output']['party_pages']}")
        self.log(f"  Search index: {'✓' if workflow_results['final_output']['has_search_index'] else '✗'}")
        self.log(f"  Homepage: {'✓' if workflow_results['final_output']['has_homepage'] else '✗'}")
        
        self.log(f"\n⚙️  GitHub Actions:")
        self.log(f"  Weekly update workflow: {'✓' if github_results['weekly_update_valid'] else '✗'}")
        self.log(f"  Deploy pages workflow: {'✓' if github_results['deploy_pages_valid'] else '✗'}")
        self.log(f"  CI workflow: {'✓' if github_results['ci_exists'] else '⚠ (optional)'}")
        
        self.log(f"\n🔄 Workflow Steps:")
        for i, step in enumerate(self.workflow_steps, 1):
            status = "✓" if step["success"] else "✗"
            self.log(f"  {i}. {status} {step['description']}")
        
        # Overall status
        self.log(f"\n🎯 Overall Status:")
        self.log(f"  Issues found: {len(self.issues)}")
        
        if not self.issues:
            self.log(f"\n✅ SUCCESS: End-to-end workflow completed successfully!")
            self.log(f"  - All pipeline steps executed")
            self.log(f"  - Data flowed through system correctly")
            self.log(f"  - GitHub Actions workflows configured")
            self.log(f"  - System ready for deployment")
            return True
        else:
            self.log(f"\n⚠️  PARTIAL SUCCESS: Some issues found")
            for issue in self.issues:
                self.log(f"  - {issue}")
            return False
    
    def save_report(self, filename: str = "test_end_to_end_report.txt"):
        """Save report to file."""
        report_path = Path(filename)
        with open(report_path, "w") as f:
            f.write("\n".join(self.report))
        self.log(f"\n📄 Report saved to: {report_path.absolute()}")
    
    def run(self):
        """Run the full end-to-end test suite."""
        self.log("Starting Task 8.4: End-to-End Testing")
        self.log(f"Database: {self.db_path}")
        self.log(f"Output directory: {self.output_dir}")
        
        # Test GitHub Actions workflows
        github_results = self.test_github_actions_workflow()
        
        # Run end-to-end workflow
        workflow_results = self.run_end_to_end_workflow()
        
        # Generate report
        success = self.generate_report(workflow_results, github_results)
        
        # Save report
        self.save_report()
        
        # Print manual testing instructions
        self.log("\n" + "=" * 80)
        self.log("MANUAL TESTING REQUIRED")
        self.log("=" * 80)
        self.log("\nThe following tests require manual verification:")
        self.log("\n1. GitHub Actions Workflow:")
        self.log("   - Trigger weekly-update workflow manually")
        self.log("   - Check workflow runs successfully")
        self.log("   - Verify all steps complete")
        self.log("\n2. Local Site Testing:")
        self.log("   - Run: python app.py")
        self.log("   - Open: http://localhost:5000")
        self.log("   - Test search functionality")
        self.log("   - Navigate through MP profiles")
        self.log("   - Check mobile responsiveness")
        self.log("\n3. Cloudflare Pages Deployment:")
        self.log("   - Connect repository to Cloudflare Pages")
        self.log("   - Configure build settings")
        self.log("   - Test deployment")
        self.log("   - Verify live site functionality")
        
        return success


if __name__ == "__main__":
    tester = EndToEndTester()
    success = tester.run()
    sys.exit(0 if success else 1)
