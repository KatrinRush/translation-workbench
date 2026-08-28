# Book Cover Implementation

This document describes the book cover functionality implementation for the Translation Workbench.

## Features

### 1. Automatic Cover Detection from EPUB
When an EPUB file is uploaded, the system automatically:
- Detects and extracts the cover image from the EPUB manifest (if available)
- Supports multiple cover detection methods:
  - Items marked with `properties="cover-image"` in the manifest
  - Common cover ID patterns (cover, cover-image, img-cover)
- Validates the image format (JPEG, PNG, GIF, WebP)
- Stores the cover image in the database as a BLOB

### 2. Cover Display
- Covers are displayed in the project card on the main page (180x260px)
- Covers are also displayed in the project workspace
- If no cover is available, a placeholder ("📚 Нема обкладинки") is shown
- Covers are cached and persist across page reloads and server restarts

### 3. Manual Cover Upload
Users can manually upload a cover image via:
- Upload button in the project workspace
- Supports common image formats (JPEG, PNG, GIF, WebP)
- Maximum file size: 10 MB
- When uploaded manually, the cover is marked as user-provided

### 4. Cover Replacement Logic
When replacing an EPUB file:
- **If new EPUB has a cover**: Use the new cover (overwrite auto-detected cover)
- **If new EPUB has NO cover but old auto-cover exists**: Clear the old auto-cover
- **If old cover was user-uploaded**: PRESERVE it (don't overwrite automatically)

This ensures that manually uploaded covers are never lost during EPUB replacements.

## Architecture

### Database Schema
Added two new columns to `book_documents` table:
- `cover_image BLOB` - Stores the binary image data
- `cover_uploaded_by_user INTEGER` - Flag to distinguish auto-detected (0) vs user-uploaded (1) covers

### Backend API Endpoints

#### GET /api/projects/{projectId}/cover
Returns the cover image as binary data
- Status 200: Image returned with appropriate Content-Type
- Status 404: No cover found

#### POST /api/projects/{projectId}/cover
Uploads a new cover image (multipart form-data)
- Status 200: Cover uploaded successfully
- Status 400: Invalid input or file too large
- Status 422: Failed to process image

#### DELETE /api/projects/{projectId}/cover
Removes the cover image
- Status 204: Cover deleted successfully
- Status 404: Project not found

### Storage Methods
- `get_project_cover(project_id)` - Retrieve cover bytes
- `set_project_cover(project_id, image_data)` - Upload cover (marks as user-provided)
- `clear_project_cover(project_id)` - Remove cover

## Testing

### E2E Tests
Located in `e2e/cover.spec.ts`, tests the following scenarios:

1. **EPUB with cover → cover appears**
   - Upload an EPUB with embedded cover
   - Verify cover is displayed in workspace
   - Verify cover is accessible via API

2. **Reload/reopen → cover persists**
   - Upload EPUB with cover
   - Reload page
   - Navigate back to project
   - Verify cover still exists and is identical

3. **EPUB without cover → placeholder shown**
   - Upload EPUB without cover
   - Verify placeholder is displayed
   - Verify no cover image element exists

4. **Manual upload → cover changed**
   - Upload EPUB without cover
   - Manually upload a cover image
   - Verify placeholder is replaced with image

5. **Replace EPUB → cover behavior**
   - Upload EPUB with cover
   - Replace with EPUB without cover
   - Verify auto-detected cover is cleared
   - Verify user-uploaded covers are preserved

### Running Tests

```bash
# Install dependencies
npm install

# Run E2E tests
npx playwright test

# Run tests in UI mode
npx playwright test --ui

# Run specific test file
npx playwright test e2e/cover.spec.ts
```

## UI Components

### Project Card (Main Page)
- Cover image displayed as 180x260px thumbnail with 1:1.44 aspect ratio
- Placeholder shown if no cover
- Covers are clickable (opens project)

### Project Workspace
- Full cover display section with upload/remove buttons
- Cover shown at full size or as placeholder
- "Upload Cover" button to add manual cover
- "Remove Cover" button (only visible when cover exists)

## Frontend Components

### New Elements
- `#upload-cover-button` - Trigger cover upload dialog
- `#remove-cover-button` - Remove current cover
- `#cover-file-input` - Hidden file input for cover selection
- `#workspace-cover` - Cover display container
- `#project-cover-section` - Entire cover section in project workspace

### New Functions
- `uploadProjectCover(projectId, file)` - Upload cover image
- `deleteProjectCover(projectId)` - Delete cover
- `renderProjectCover(projectId)` - Display cover or placeholder
- `showCoverPlaceholder()` - Show placeholder UI

### Event Listeners
- Upload button click → open file picker
- Cover file selection → upload image
- Remove button click → delete cover (with confirmation)

## Styling

### CSS Classes
- `.project-cover` - Cover container in project card (180x260px)
- `.project-cover-placeholder` - Placeholder text
- `.workspace-cover-container` - Container for workspace cover section
- `.workspace-cover` - Cover display area in workspace
- `.workspace-cover-placeholder` - Placeholder in workspace
- `.cover-actions` - Action buttons container

## Data Persistence

Covers are stored in:
1. Database: `book_documents.cover_image` (BLOB)
2. Database: `book_documents.cover_uploaded_by_user` (flag)
3. Retrieved via API endpoints as needed

## Non-Breaking Changes

- No changes to existing project model or API
- Backward compatible: existing projects without covers work fine
- No impact on paragraph/position/brief/references logic
- Existing upload flow remains unchanged

## Deployment Considerations

1. Database migration: Schema changes are applied automatically on first run
2. No external dependencies added (uses built-in Python image validation)
3. Cover file size limited to 10 MB
4. Supported formats: JPEG, PNG, GIF, WebP
5. Covers are stored in database, no file system dependencies
