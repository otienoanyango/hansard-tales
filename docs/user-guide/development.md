# Hansard Tales Development Guide

## Getting Started

### Prerequisites
- Go 1.21+
- Python 3.11+  
- Node.js 18+
- Docker & Docker Compose
- Git

### Initial Setup
1. **Run the setup script**:
   ```bash
   chmod +x tools/local-setup.sh
   ./tools/local-setup.sh
   ```

2. **Start local services**:
   ```bash
   docker-compose up -d
   ```

3. **Verify everything works**:
   ```bash
   ./tools/run-local-tests.sh
   ```

## Feature Branch Workflow

### Creating a Feature Branch
```bash
# 1. Get latest main
git checkout main
git pull origin main

# 2. Create feature branch (use task number from MVP checklist)
git checkout -b feature/task-2.1-go-development-env

# 3. Implement the task
# ... make your changes ...

# 4. Test locally before PR
./tools/run-local-tests.sh

# 5. Format and lint
cd data-processing/go-functions && go fmt ./...
cd ../../data-processing/python-functions && black .
cd ../../frontend/web && npm run format

# 6. Commit and push
git add .
git commit -m "feat: implement task 2.1 - Go development environment setup"
git push origin feature/task-2.1-go-development-env

# 7. Create PR using GitHub interface
# 8. Merge after all checks pass
```

### PR Checklist Template
When creating a PR, ensure all items in the template are checked:

- [ ] ✅ All tests pass locally
- [ ] ✅ Code coverage maintained or improved
- [ ] ✅ Code formatted correctly
- [ ] ✅ Linting passes with no new warnings
- [ ] ✅ Documentation updated if needed

## Testing Strategy

### Running Tests Locally

#### All Tests
```bash
./tools/run-local-tests.sh
```

#### Go Tests Only
```bash
cd data-processing/go-functions
go test ./... -v -cover
```

#### Python Tests Only
```bash
cd data-processing/python-functions
source ../../.venv/bin/activate
pytest --cov=. --cov-report=term-missing -v
```

#### Frontend Tests Only
```bash
cd frontend/web
npm test -- --coverage
```

### Coverage Requirements
- **Go Functions**: >85% coverage
- **Python Functions**: >90% coverage (critical for AI accuracy)
- **Frontend**: >75% coverage

### Writing Good Tests

#### Go Function Tests
```go
func TestFunctionName(t *testing.T) {
    // Use table-driven tests
    tests := []struct {
        name     string
        input    string
        expected string
        wantErr  bool
    }{
        // Test cases...
    }
    
    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            result, err := FunctionName(tt.input)
            if tt.wantErr {
                assert.Error(t, err)
            } else {
                assert.NoError(t, err)
                assert.Equal(t, tt.expected, result)
            }
        })
    }
}
```

#### Python Function Tests
```python
class TestFunctionName:
    """Test function description"""
    
    def test_success_case(self):
        """Test successful execution"""
        result = function_name("test_input")
        assert result == "expected_output"
    
    def test_error_case(self):
        """Test error handling"""
        with pytest.raises(ValueError, match="expected error message"):
            function_name("invalid_input")
```

#### React Component Tests
```typescript
describe('ComponentName', () => {
    test('renders correctly', () => {
        render(<ComponentName prop="value" />);
        expect(screen.getByTestId('component-element')).toBeInTheDocument();
    });
    
    test('handles user interaction', () => {
        const mockCallback = jest.fn();
        render(<ComponentName onAction={mockCallback} />);
        
        fireEvent.click(screen.getByRole('button'));
        expect(mockCallback).toHaveBeenCalled();
    });
});
```

## Code Quality Standards

### Formatting
- **Go**: `go fmt` (automatic)
- **Python**: `black` with 88-character line limit
- **TypeScript**: `prettier` with 80-character preferred limit

### Linting
- **Go**: `golangci-lint run`
- **Python**: `flake8` with mypy type checking  
- **TypeScript**: `eslint` with TypeScript rules

### Commit Messages
```bash
# Format: type: brief description (50 chars or less)
feat: add MP performance calculation
fix: handle empty PDF documents gracefully
docs: update API usage examples  
test: add unit tests for date parsing
refactor: simplify statement filtering logic
```

## Local Development Environment

### Services Running in Docker
- **PostgreSQL**: localhost:5432 (hansard_tales_dev/dev_user/dev_password)
- **Redis**: localhost:6379 (for caching)
- **LocalStack**: localhost:4566 (AWS services emulation)

### Environment Variables
Copy `.env.example` to `.env` and fill in:
- Database connection strings
- GCP project configuration
- API keys for external services
- Feature flags for development

### VS Code Configuration
The setup script creates:
- **settings.json**: Editor configuration optimized for the project
- **extensions.json**: Recommended extensions for all languages
- **launch.json**: Debug configurations (to be added)

### Troubleshooting

#### Tests Failing
1. **Check formatting**: Run formatters for your language
2. **Check dependencies**: Ensure all packages installed
3. **Check environment**: Verify Docker services running
4. **Check coverage**: Add tests if coverage dropped

#### Build Failing  
1. **TypeScript errors**: Run `npm run type-check`
2. **Go build errors**: Run `go build ./...`
3. **Python import errors**: Check virtual environment activated

#### Local Services Issues
```bash
# Restart Docker services
docker-compose down
docker-compose up -d

# Check service health
docker-compose ps
docker-compose logs [service-name]
```

## Project Structure

```
hansard-tales/
├── .github/workflows/          # CI/CD pipelines
├── data-processing/            # Data pipeline components
│   ├── go-functions/          # Fast PDF processing
│   └── python-functions/      # AI/ML processing
├── frontend/web/              # Next.js website
├── backend/                   # Optional API services
├── infrastructure/terraform/   # Infrastructure as Code
├── tests/                     # All test suites
├── tools/                     # Development scripts
├── docs/                      # Documentation
└── config/                    # Configuration files
```

## Development Principles

Based on `.claude-skills` file:
- **Simplicity First**: Choose simplest solution that works
- **Small Changes**: Each PR should be reviewable in 10-15 minutes
- **Test Everything**: Comprehensive testing before merge
- **Document Why**: Explain decisions, not just implementation
- **Fail Fast**: Fix CI failures immediately

## Next Steps

After completing the initial setup:
1. **Implement Task 2.1**: Go development environment
2. **Implement Task 2.2**: Hansard scraper in Go
3. **Add comprehensive tests** for each component
4. **Follow feature branch workflow** for all changes

## Support

- **GitHub Issues**: Report bugs and request features
- **Documentation**: Check `/docs` directory for detailed guides
- **CI/CD**: All workflows automatically validate changes
- **Monitoring**: Production monitoring dashboards available

Remember: All code must pass tests and maintain coverage before merging to main!
