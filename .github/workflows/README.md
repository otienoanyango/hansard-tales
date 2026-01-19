# GitHub Actions Workflows

This directory contains automated workflows for the Hansard Tales project.

## Workflows

### CI (`ci.yml`)

Runs automated tests and checks on every push and pull request.

**Triggers:**
- Push to `main` branch
- Push to any `feat/**` branch
- Pull requests to `main` branch

**Jobs:**
- Runs tests on Python 3.11 and 3.12
- Executes pytest with parallel execution (`-n auto`)
- Generates coverage reports
- Uploads coverage to Codecov (Python 3.11 only)
- Enforces 80% minimum coverage threshold

**Requirements:**
- All tests must pass
- Coverage must be ≥80%

### Auto Merge (`auto-merge.yml`)

Automatically merges pull requests from feature branches when CI checks pass.

**Triggers:**
- Pull requests opened, synchronized, or reopened
- Only for PRs targeting `main` branch
- Only for branches starting with `feat/`

**Behavior:**
1. Waits for CI workflow to complete successfully
2. Automatically enables auto-merge with squash strategy
3. PR will be merged when all required checks pass

**Requirements:**
- PR must be from a `feat/` branch
- All CI checks must pass
- Repository must have auto-merge enabled in settings

## Setup Instructions

### 1. Enable Auto-Merge in Repository Settings

1. Go to repository Settings → General
2. Scroll to "Pull Requests" section
3. Check "Allow auto-merge"
4. Check "Automatically delete head branches"

### 2. Configure Branch Protection (Optional but Recommended)

1. Go to Settings → Branches
2. Add branch protection rule for `main`:
   - Require pull request reviews before merging (optional)
   - Require status checks to pass before merging
   - Require branches to be up to date before merging
   - Status checks that are required: `test`

### 3. Add Codecov Token (Optional)

If you want coverage reporting:

1. Sign up at [codecov.io](https://codecov.io)
2. Add your repository
3. Copy the upload token
4. Add to repository secrets as `CODECOV_TOKEN`

## Usage

### For Feature Development

1. Create feature branch: `git checkout -b feat/4.1-jinja2-templating`
2. Make changes and commit
3. Push branch: `git push origin feat/4.1-jinja2-templating`
4. Create pull request to `main`
5. CI will run automatically
6. If all checks pass, PR will auto-merge
7. Branch will be automatically deleted after merge

### Manual Merge Override

If you need to merge manually:
1. Disable auto-merge on the PR
2. Merge using GitHub UI after reviews

## Troubleshooting

### Auto-merge not working

- Check that branch name starts with `feat/`
- Verify auto-merge is enabled in repository settings
- Ensure CI workflow completed successfully
- Check GitHub Actions logs for errors

### CI failing

- Review test output in Actions tab
- Check coverage report for uncovered code
- Ensure all dependencies are in `pyproject.toml`
- Verify Python version compatibility (3.11+)

### Coverage below threshold

- Add tests for uncovered code
- Current threshold: 80%
- View detailed coverage report in CI logs
