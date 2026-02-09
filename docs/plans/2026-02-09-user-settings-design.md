# User Settings Endpoint Design

## Overview

Add a user settings endpoint that allows authenticated users to read and update their preferences. Initially supports `theme` and `display_name` settings, stored in a key-value table for flexibility.

## Data Layer

### New table: `user_settings`

| Column       | Type           | Constraints                                      |
| ------------ | -------------- | ------------------------------------------------ |
| `id`         | `serial`       | primary key                                      |
| `user_id`    | `integer`      | not null, references `users(id)`, unique(user_id, key) |
| `key`        | `varchar(255)` | not null, unique(user_id, key)                   |
| `value`      | `varchar(1024)`| not null                                         |
| `updated_at` | `timestamp`    | not null, default now()                          |

Composite unique constraint on `(user_id, key)` ensures one value per setting per user.

### Allowed keys and valid values

- `theme`: `"light"` | `"dark"` | `"system"`
- `display_name`: any non-empty string, max 255 chars

### Defaults

- `theme` → `"system"`
- `display_name` → `""`

## API Endpoints

### `GET /api/settings` (authenticated)

Returns all settings for the current user as a flat object. Missing keys return their defaults.

```json
{ "theme": "system", "display_name": "" }
```

### `PATCH /api/settings` (authenticated)

Accepts a partial object of settings to upsert.

```json
// Request
{ "theme": "dark" }

// Response 200
{ "theme": "dark", "display_name": "" }
```

Returns the full settings object after the update (same shape as GET).

### Error responses

- Unknown key → `400 { error: "Unknown setting: foo" }`
- Invalid value → `400 { error: "Invalid value for theme: must be one of light, dark, system" }`
- Empty body → `400 { error: "No settings provided" }`
- Not authenticated → `401 { error: "Not authenticated" }`

## Implementation Details

### Validation map

```typescript
const SETTINGS_VALIDATORS: Record<string, { default: string; validate: (v: string) => boolean }> = {
  theme: { default: 'system', validate: v => ['light', 'dark', 'system'].includes(v) },
  display_name: { default: '', validate: v => v.length > 0 && v.length <= 255 },
};
```

### Files to create/modify

- **`backend/src/db/schema.ts`** — Add `userSettings` table definition
- **`backend/src/routes/settings.ts`** — New route file with GET and PATCH handlers
- **`backend/src/app.ts`** — Register settings routes
- **`backend/test/settings.test.ts`** — Tests for both endpoints

### Upsert strategy

PATCH uses `INSERT ... ON CONFLICT (user_id, key) DO UPDATE SET value = ..., updated_at = now()` per key. No read-before-write needed.

### Tests

- GET returns defaults when no settings exist
- PATCH upserts a single setting
- PATCH upserts multiple settings
- PATCH rejects unknown keys
- PATCH rejects invalid theme values
- Both endpoints return 401 when not authenticated
- Response always includes all keys with defaults filled in
