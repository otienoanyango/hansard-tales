# GitHub Actions Weekly Workflow - PR Creation Fix

## Problem
The weekly Hansard update workflow was attempting to push changes directly to the `main` branch, which is protected and requires pull request reviews. This would cause the workflow to fail when trying to commit database and PDF updates.

## Solution
Modified the workflow to create pull requests instead of pushing directly to main.

### Changes Made

1. **Added PR Permission**
   ```yaml
   permissions:
     contents: write
     pages: write
     id-token: write
     pull-requests: write  # Added for PR creation
   ```

2. **Replaced Direct Push with PR Creation**
   - Removed the "Commit and push changes" step
   - Added "Create Pull Request with changes" step using `peter-evans/create-pull-request@v6`
   - Creates automated branch: `automated/weekly-update-{run_number}`
   - Auto-deletes branch after PR is merged/closed

3. **PR Configuration**
   - **Title**: "Weekly Hansard Update - YYYY-MM-DD"
   - **Body**: Includes date, workflow run link, changes summary, and review checklist
   - **Labels**: `automation`, `weekly-update`
   - **Assignee**: Repository owner (auto-assigned)
   - **Files**: Only commits `data/hansard.db` and `data/pdfs/*.pdf`

4. **Updated Workflow Summary**
   - Changed "Commit & Push" reference to "Pull Request"
   - Added PR number and URL to summary when PR is created

5. **Updated Failure Notification**
   - Changed "Commit & Push" reference to "Pull Request Creation"

## How It Works

1. **Weekly Schedule**: Runs every Sunday at 2 AM EAT (23:00 UTC Saturday)
2. **Scrape & Process**: Downloads new Hansard PDFs and processes them
3. **Update Database**: Adds new statements to `data/hansard.db`
4. **Generate Site**: Creates search index and static site
5. **Create PR**: Creates a pull request with database and PDF changes
6. **Deploy**: Deploys to GitHub Pages (happens regardless of PR status)

## Manual Testing

To test the workflow manually:

1. Go to **Actions** tab in GitHub
2. Select **Weekly Hansard Update** workflow
3. Click **Run workflow** button
4. Select branch: `fix/cloudflare-spacy-download`
5. Click **Run workflow**

Expected outcome:
- Workflow completes successfully
- A new PR is created with title "Weekly Hansard Update - YYYY-MM-DD"
- PR is assigned to repository owner
- PR contains database and PDF changes
- GitHub Pages deployment succeeds

## Merging PRs

After the workflow creates a PR:

1. Review the PR to ensure:
   - Database file size is reasonable (should be ~500 KB)
   - New PDF files are present in `data/pdfs/`
   - No unexpected files are included

2. Merge the PR to deploy updates to production

3. The automated branch will be deleted automatically

## Alternative Approach

If you prefer direct pushes instead of PRs, you can:

1. Go to **Settings** → **Branches** → **Branch protection rules** for `main`
2. Add `github-actions[bot]` to "Allow specified actors to bypass required pull requests"
3. Revert this workflow change to use direct push

However, the PR approach is recommended as it:
- Provides visibility into weekly updates
- Allows review before deployment
- Creates an audit trail
- Prevents accidental bad data from reaching production

## Files Modified

- `.github/workflows/weekly-update.yml` - Updated to create PRs instead of direct push

## Branch

- `fix/cloudflare-spacy-download` - Contains this fix along with Cloudflare build fixes

## Status

✅ **Complete** - Committed and pushed to GitHub
⏳ **Pending** - Needs manual testing via workflow dispatch
⏳ **Pending** - Needs user review and merge to main
