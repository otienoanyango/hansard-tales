#!/bin/bash
# Run all tests locally before creating PR - calls subproject test scripts

set -e

echo "🧪 Hansard Tales - Running All Local Tests"
echo "========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track test results
RESULTS=()
OVERALL_SUCCESS=true

echo "📁 Current directory: $(pwd)"

# Function to run subproject tests
run_subproject_test() {
    local project_name=$1
    local test_script=$2
    
    echo ""
    echo -e "${YELLOW}Testing $project_name...${NC}"
    
    if [ -f "$test_script" ]; then
        if bash "$test_script"; then
            echo -e "${GREEN}✅ $project_name tests passed${NC}"
            RESULTS+=("$project_name:PASSED")
        else
            echo -e "${RED}❌ $project_name tests failed${NC}"
            RESULTS+=("$project_name:FAILED")
            OVERALL_SUCCESS=false
        fi
    else
        echo -e "${YELLOW}⚠️  $project_name test script not found: $test_script${NC}"
        RESULTS+=("$project_name:SKIPPED")
    fi
}

# Run each subproject's tests
run_subproject_test "Go Functions" "data-processing/go-functions/test.sh"
run_subproject_test "Python Functions" "data-processing/python-functions/test.sh"
run_subproject_test "Frontend" "frontend/web/test.sh"

echo ""
echo "📊 Test Summary"
echo "==============="

# Print results
for result in "${RESULTS[@]}"; do
    IFS=':' read -r project status <<< "$result"
    case $status in
        "PASSED")
            echo -e "$project: ${GREEN}✅ PASSED${NC}"
            ;;
        "FAILED")
            echo -e "$project: ${RED}❌ FAILED${NC}"
            ;;
        "SKIPPED")
            echo -e "$project: ${YELLOW}⚠️  SKIPPED${NC}"
            ;;
    esac
done

# Overall result
echo ""
if [ "$OVERALL_SUCCESS" = true ]; then
    echo -e "${GREEN}🎉 ALL TESTS PASSED! Ready to create PR.${NC}"
    exit 0
else
    echo -e "${RED}❌ Some tests failed. Fix issues before creating PR.${NC}"
    echo ""
    echo "💡 How to fix:"
    echo "  - Run individual test scripts: ./data-processing/go-functions/test.sh"
    echo "  - Check subproject directories for detailed error logs"
    echo "  - Ensure all dependencies are installed"
    echo "  - Run formatters and linters in each subproject"
    exit 1
fi
