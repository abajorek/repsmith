# RepSmith - Technical Documentation

## Architecture Overview

RepSmith follows a classic web application architecture:
- **Backend**: Flask REST API with SQLAlchemy ORM
- **Frontend**: Vanilla JavaScript with Tailwind CSS
- **Database**: SQLite for simplicity and portability
- **Parser**: BeautifulSoup4 for HTML parsing

## Backend Components

### Database Models (`backend/models.py`)

#### Song Model
The core entity representing a song with all metadata:

```python
class Song(Base):
    # Basic Information
    title: str (required)
    alternate_titles: str

    # Musical Attributes
    tone_set: str (indexed)
    range: str
    starting_pitch: str
    meter: str
    tempo: str
    tempo_min: int  # Extracted for range queries
    tempo_max: int
    character: str

    # Pedagogical Context
    teaching_purpose: str
    sequence_level: str
    cultural_origin: str
    game_type: str (indexed)
    source: str
    borrowed_from: str

    # Content
    lyrics: text
    directions: text
    keywords: str (indexed)
    notes: text
    notation_reference: str
    similar_songs: str

    # Metadata
    created_at: datetime
    updated_at: datetime
```

#### Collection Model
For organizing songs into custom groups:

```python
class Collection(Base):
    name: str (unique)
    description: str
    songs: relationship (many-to-many)
```

### HTML Parser (`backend/parser.py`)

#### SongHTMLParser Class

The parser handles structural variations in mysongcollection.com HTML files.

**Key Methods:**

- `parse_file(file_path)` - Entry point for file parsing
- `parse_html(html_content, file_path)` - Main parsing logic
- `_extract_title(soup)` - Extract from `<h2>` tag
- `_extract_table_metadata(table, song_data)` - Parse metadata table rows
- `_extract_tempo(soup)` - Handle both `l=` and `I =` patterns
- `_extract_meter(soup)` - Extract time signature from notation
- `_extract_directions(soup)` - Find "Directions:" or "Motions:" blocks
- `_extract_lyrics(soup)` - Extract from notation table

**Parsing Strategy:**

1. Find metadata table (contains S.S.P., R.S.P.)
2. Extract rows in order:
   - Row 1: S.S.P. (left), Game Type (right)
   - Row 2: R.S.P. (left), Keywords (right)
   - Row 3: Tempo (left)
   - Row 4: Character (left, optional), Tone Set (right)
3. Handle missing/optional fields gracefully
4. Extract tempo as min/max for range queries
5. Parse meter from notation table font tags
6. Find directions by label keywords
7. Extract source and attribution

**Error Handling:**

- Missing fields leave blank (don't fail entire import)
- Warnings for critical fields (title, tone set)
- Unparseable tempo handled gracefully
- Continue on errors, collect warnings

### Flask Application (`backend/app.py`)

#### API Endpoints

**Upload & Import**
```
POST /api/upload
- Accepts: multipart/form-data with files[]
- Returns: parsed_songs[], errors[]
- Max file size: 16MB
```

**Songs CRUD**
```
GET /api/songs
- Query params: tone_set, game_type, keywords, tempo_min, tempo_max, search
- Pagination: page, per_page
- Sorting: sort_by, sort_order
- Returns: songs[], total, page, pages

POST /api/songs
- Body: {songs: [{song_data}, ...]}
- Creates multiple songs
- Returns: created songs[]

GET /api/songs/<id>
- Returns: song object

PUT /api/songs/<id>
- Body: {field: value, ...}
- Updates song
- Returns: updated song

DELETE /api/songs/<id>
- Deletes song
- Returns: success message
```

**Search**
```
GET /api/songs/search
- Query param: q (free text search)
- Searches: title, alternate_titles, lyrics, keywords
- Returns: songs[], count
```

**Analytics**
```
GET /api/analytics/dashboard
- Returns:
  - total_songs
  - tone_set_distribution[]
  - game_type_distribution[]
  - tempo_distribution[]
  - source_distribution[]
```

**Collections**
```
GET /api/collections
- Returns: collections[]

POST /api/collections
- Body: {name, description}
- Creates collection

POST /api/collections/<id>/songs
- Body: {song_id}
- Adds song to collection

DELETE /api/collections/<id>/songs
- Body: {song_id}
- Removes song from collection
```

**Export**
```
GET /api/export/csv
- Returns: CSV file download
- Filename: repsmith_export.csv
```

## Frontend Components

### HTML Structure (`frontend/templates/index.html`)

**Tab System:**
- Import Tab: File upload and preview
- Browse Tab: Search, filter, and list songs
- Dashboard Tab: Analytics and gap analysis

**Modal:**
- Song detail view with all metadata

### JavaScript Application (`frontend/static/js/app.js`)

**Global State:**
```javascript
let parsedSongs = [];      // Staging area for imported songs
let currentSongs = [];     // Currently displayed songs
let currentPage = 1;       // Pagination
let currentSortBy = 'title';
let currentSortOrder = 'asc';
```

**Key Functions:**

- `switchTab(tabName)` - Tab navigation
- `uploadFiles()` - Handle file upload and parsing
- `displayPreview(songs)` - Show parsed songs before saving
- `saveAllSongs()` - Commit to database
- `loadSongs(page)` - Fetch and display songs
- `filterSongs()` - Apply search/filter criteria
- `viewSong(id)` - Show modal with full details
- `loadDashboard()` - Fetch and render analytics
- `renderBarChart(container, data, label)` - Simple bar charts
- `exportCSV()` - Download CSV export

## Database Schema

### Tables

**songs**
```sql
CREATE TABLE songs (
    id INTEGER PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    alternate_titles VARCHAR(500),
    tone_set VARCHAR(100),
    range VARCHAR(50),
    starting_pitch VARCHAR(50),
    meter VARCHAR(20),
    tempo VARCHAR(50),
    tempo_min INTEGER,
    tempo_max INTEGER,
    character VARCHAR(100),
    key_signature VARCHAR(20),
    melodic_elements TEXT,
    rhythmic_elements TEXT,
    teaching_purpose TEXT,
    sequence_level VARCHAR(50),
    cultural_origin VARCHAR(100),
    game_type VARCHAR(100),
    source TEXT,
    borrowed_from VARCHAR(200),
    lyrics TEXT,
    directions TEXT,
    keywords VARCHAR(500),
    notes TEXT,
    notation_reference VARCHAR(500),
    similar_songs TEXT,
    created_at DATETIME,
    updated_at DATETIME
);

CREATE INDEX idx_songs_title ON songs(title);
CREATE INDEX idx_songs_tone_set ON songs(tone_set);
CREATE INDEX idx_songs_game_type ON songs(game_type);
CREATE INDEX idx_songs_keywords ON songs(keywords);
```

**collections**
```sql
CREATE TABLE collections (
    id INTEGER PRIMARY KEY,
    name VARCHAR(200) NOT NULL UNIQUE,
    description TEXT,
    created_at DATETIME
);
```

**song_collections** (many-to-many)
```sql
CREATE TABLE song_collections (
    song_id INTEGER REFERENCES songs(id),
    collection_id INTEGER REFERENCES collections(id)
);
```

## Parser Field Extraction Rules

### Field Priority and Patterns

| Priority | Field | HTML Pattern | Required | Notes |
|----------|-------|--------------|----------|-------|
| 1 | Title | `<h2>` text | Yes | Critical warning if missing |
| 2 | Tone Set | Right-aligned cell with pattern `[\(\)drmfsl,\s]+` | Important | Warning if missing |
| 3 | Game Type | First right-aligned cell with game keywords | No | Common values: circle game, Play Party, singing game |
| 4 | Starting Pitch | `S.S.P.:` in left cell | No | Examples: "Eb", "c = sol" |
| 5 | Range | `R.S.P.:` in left cell | No | Examples: "Eb - F", "c = sol" |
| 6 | Tempo | `l=` or `I =` pattern | No | Extracts min/max for queries |
| 7 | Keywords | Second right-aligned cell (not tone set) | No | Comma-separated or single words |
| 8 | Character | Fourth row left cell (non-empty) | No | Examples: "briskly", "gently" |
| 9 | Meter | `<font size="5">N<br>N</font>` in notation table | No | Examples: "2/4", "6/8" |
| 10 | Directions | Text after "Directions:" or "Motions:" | No | Full paragraph extracted |
| 11 | Lyrics | Text from notation table | No | Excludes metadata |
| 12 | Source | Text before "Borrowed from:" | No | Book/collection reference |
| 13 | Borrowed From | Text after "Borrowed from:" | No | Teacher/contributor name |

### Tempo Parsing Logic

```python
# Pattern 1: l=120-136
match = re.search(r'l\s*=\s*([\d\-]+)', text, re.IGNORECASE)

# Pattern 2: I = 96
if not match:
    match = re.search(r'I\s*=\s*([\d\-]+)', text)

# Extract min/max
tempo_parts = tempo_str.split('-')
tempo_min = int(tempo_parts[0])
tempo_max = int(tempo_parts[-1])  # Same as min if no range
```

### Tone Set Recognition

Pattern: `[\(\)drmfsl,\s]+`

Examples:
- `s-m`
- `d-r-m`
- `(d)rmfsl`
- `s,l, (d)rm sl`

Distinguishes from keywords by checking for solfege syllables: d, r, m, f, s, l

## Performance Considerations

### Database Queries

**Indexed fields** for fast searches:
- `title` - Full-text search
- `tone_set` - Exact and partial matches
- `game_type` - Filter queries
- `keywords` - Full-text search

**Pagination** implemented server-side:
- Default: 20 songs per page
- Prevents loading entire dataset

### File Upload

- Max file size: 16MB per file
- Batch upload supported
- Files saved to `uploads/` directory
- Original HTML preserved for notation reference

### Parser Optimization

- Single-pass parsing
- Early exit on critical errors
- Minimal regex operations
- Warnings collected, don't block

## Testing

### Test Files

Located in `tests/`:
- `test_chicken_fencepost.html` - Full metadata example
- `test_tisket_tasket.html` - Missing character field
- `test_starlight.html` - Alternate title, different tempo

### Manual Testing

```bash
# Test parser directly
cd backend
python parser.py

# Test with specific file
python -c "from parser import parse_song_file; import json; print(json.dumps(parse_song_file('../tests/test_chicken_fencepost.html'), indent=2))"

# Initialize fresh database
rm ../data/repsmith.db
python database.py

# Start server
python app.py
```

### API Testing

```bash
# Test upload
curl -X POST http://localhost:5000/api/upload \
  -F "files[]=@../tests/test_chicken_fencepost.html"

# Test search
curl "http://localhost:5000/api/songs?search=chicken"

# Test filter
curl "http://localhost:5000/api/songs?tone_set=s-m&game_type=circle"
```

## Deployment Considerations

### Local Deployment (Recommended)

- SQLite database for single-user
- No authentication needed
- Run on localhost
- Data stored locally

### Future Multi-User Deployment

If deploying for multiple users:

1. **Switch to PostgreSQL/MySQL**
   ```python
   DATABASE_URL = 'postgresql://user:pass@localhost/repsmith'
   ```

2. **Add Authentication**
   - Flask-Login or JWT
   - User model with song ownership
   - Collection permissions

3. **Configure WSGI Server**
   ```bash
   gunicorn -w 4 -b 0.0.0.0:5000 backend.app:app
   ```

4. **Add Nginx Reverse Proxy**
   ```nginx
   location / {
       proxy_pass http://localhost:5000;
   }
   ```

5. **Enable HTTPS**
   - Let's Encrypt certificate
   - Redirect HTTP to HTTPS

## Extending RepSmith

### Adding New Fields

1. Add column to `Song` model in `models.py`
2. Add extraction logic to parser
3. Update `to_dict()` method
4. Add to frontend display
5. Run migration (if using Alembic)

### Adding New Features

**Manual Entry Form:**
```javascript
// Frontend: Create form with all fields
// Backend: Validate and create Song object
```

**PDF Export:**
```python
# Use ReportLab or WeasyPrint
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate
```

**Advanced Analytics:**
```python
# Add new analytics endpoints
@app.route('/api/analytics/sequence-coverage')
def sequence_coverage():
    # Analyze tone set progression
    # Identify missing sequence steps
```

## Troubleshooting

### Parser Issues

**Symptom:** Song not parsing correctly

**Debug Steps:**
1. Print HTML structure: `print(soup.prettify())`
2. Check table structure: `tables = soup.find_all('table')`
3. Verify field patterns
4. Add debug logging to parser

### Database Issues

**Symptom:** Database locked

**Solution:**
```python
# Close all connections
SessionLocal.remove()

# Or restart server
```

**Symptom:** Schema out of date

**Solution:**
```bash
rm data/repsmith.db
python backend/database.py
```

### Frontend Issues

**Symptom:** API calls failing

**Debug:**
1. Check browser console (F12)
2. Check network tab for responses
3. Verify backend is running
4. Check CORS configuration

## Code Style

### Python
- PEP 8 compliant
- Type hints where helpful
- Docstrings for all functions
- Comments for complex logic

### JavaScript
- ES6+ features
- Async/await for API calls
- Descriptive variable names
- Comments for complex DOM manipulation

### SQL
- Snake_case for tables/columns
- Indexed foreign keys
- Explicit constraints

## Version History

### v1.0 (Current)
- HTML import with batch processing
- Full metadata extraction
- Search and filter
- Analytics dashboard
- CSV export
- Responsive UI

### Future Enhancements
- Manual entry form
- PDF export for lesson planning
- Collection management UI
- Sequence planning tools
- Import from other formats (MusicXML, etc.)
- Advanced search with boolean operators
- Song comparison tool
