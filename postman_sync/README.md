# Postman Sync

Automatically sync Fastify TypeScript routes to Postman collections while preserving manual test scripts and customizations.

## Features

- **AST-Based Parsing**: Uses tree-sitter for robust TypeScript route extraction
- **Smart Merging**: Preserves test scripts, pre-request scripts, and manual customizations
- **Git Hook Integration**: Automatically syncs on commit when route files change
- **Deprecation Tracking**: Soft-delete routes with 30-day grace period
- **Authentication Scripts**: Auto-generates JWT token management for protected routes
- **Test Generation**: Creates basic test scripts for new endpoints
- **Strict Error Handling**: Fails commits on parsing or API errors

## Installation

### Prerequisites

- Python 3.9+
- Git repository
- Postman account with API key

### Setup

> **Important:** All commands must be run from the `backend/` directory (not from inside `postman_sync/`).

```bash
cd /path/to/tracker/backend
```

1. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env and add your Postman API key and collection ID
   ```

   Required variables:
   - `POSTMAN_API_KEY` - Your Postman API key (starts with `PMAK-`)
   - `POSTMAN_COLLECTION_ID` - Target collection ID

3. **Validate setup**:
   ```bash
   python -m postman_sync validate
   ```

4. **Install Git hook** (optional but recommended):
   ```bash
   python -m postman_sync install-hook
   ```

## Usage

### Manual Sync

Sync routes to Postman:

```bash
python -m postman_sync sync
```

### Automatic Sync (Git Hook)

After installing the Git hook, syncing happens automatically when you commit changes to route files:

```bash
# Make changes to src/routes/*.ts
git add src/routes/auth.ts
git commit -m "Add new auth endpoint"
# Postman sync runs automatically
```

To bypass the hook for a specific commit:

```bash
git commit --no-verify -m "Skip sync for this commit"
```

### Commands

- `sync` - Sync routes to Postman collection
- `install-hook` - Install Git pre-commit hook
- `uninstall-hook` - Remove Git pre-commit hook
- `validate` - Validate configuration and setup
- `help` - Show help message

## Configuration

All configuration is done via environment variables in `.env`:

```bash
# Required
POSTMAN_API_KEY=PMAK-your-api-key-here
POSTMAN_COLLECTION_ID=your-collection-id-here

# Optional
POSTMAN_WORKSPACE_ID=your-workspace-id-here
POSTMAN_ROUTES_DIR=src/routes
POSTMAN_COLLECTION_FILE=postman/tracker-backend-api.postman_collection.json
POSTMAN_DEPRECATION_DAYS=30
POSTMAN_AUTO_STAGE=true
POSTMAN_FAIL_ON_ERROR=true
POSTMAN_LOG_LEVEL=INFO
```

## How It Works

### 1. Route Parsing

The tool uses tree-sitter to parse TypeScript files and extract Fastify route definitions:

```typescript
// Detects patterns like:
fastify.get('/api/users', async (request, reply) => { ... })
fastify.post('/api/users', { schema: {...} }, async (request, reply) => { ... })
```

Extracts:
- HTTP method and path
- Request/response schemas
- Rate limiting configuration
- Authentication requirements (`authVerifyHook`)
- JSDoc comments

### 2. Smart Merging

Merges parsed routes into the Postman collection while preserving:

- ✅ Test scripts
- ✅ Pre-request scripts (except auto-generated auth)
- ✅ Manual descriptions
- ✅ Example responses
- ✅ Collection variables

Changes detected:
- **New routes**: Added with generated test scripts
- **Updated routes**: URL/method updated, customizations preserved
- **Missing routes**: Marked as `**DEPRECATED**` with timestamp
- **Old deprecated**: Removed after 30 days

### 3. Authentication

For routes with `authVerifyHook`:

```typescript
fastify.get('/protected', {
  preHandler: authVerifyHook  // ← Detected!
}, async (request, reply) => { ... })
```

Auto-generates pre-request script:

```javascript
const token = pm.collectionVariables.get("jwtToken");
if (token) {
    pm.request.headers.add({
        key: "Authorization",
        value: `Bearer ${token}`
    });
}
```

### 4. Git Integration

Pre-commit hook workflow:

1. Detects if `src/routes/*.ts` files are staged
2. Runs `postman-sync sync`
3. Auto-stages updated `postman/*.json` file
4. Fails commit if sync errors occur

## Architecture

```
postman_sync/
├── config.py              # Environment configuration
├── models.py              # Domain models (Route, SyncResult)
├── cli.py                 # Command-line interface
├── parser/
│   ├── typescript_parser.py   # Tree-sitter AST parser
│   └── route_extractor.py     # Route extraction logic
├── postman/
│   ├── api_client.py          # Postman REST API client
│   ├── merger.py              # Smart merge algorithm
│   └── test_generator.py      # Test script generation
├── git/
│   ├── hook_installer.py      # Git hook management
│   └── stage_manager.py       # Git staging operations
├── sync/
│   └── engine.py              # Orchestrates workflow
└── utils/
    ├── logger.py              # Colored logging
    └── validators.py          # Validation utilities
```

## Troubleshooting

### "Collection file not found"

Make sure `POSTMAN_COLLECTION_FILE` points to the correct location relative to the backend directory.

### "Invalid Postman API key"

Verify your API key in `.env` starts with `PMAK-` and has valid permissions.

### "Postman API rate limit exceeded"

Wait 15 minutes and try again. The Postman API has rate limits.

### "Failed to parse route file"

Check TypeScript syntax in the route file. The parser expects valid TypeScript.

### Tree-sitter installation issues

If you encounter errors installing `tree-sitter-typescript`:

```bash
pip install --upgrade pip
pip install tree-sitter tree-sitter-typescript
```

## Development

### Running Tests

```bash
cd backend
pytest tests/
```

### Project Structure

See [Architecture](#architecture) section above.

## License

ISC
