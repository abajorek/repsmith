# RepSmith - Quick Start Guide

## Overview

RepSmith is a web-based repertoire management system designed for Kodály-inspired music educators. It helps you catalog, search, and analyze your song collection with detailed pedagogical metadata.

## Features

✅ **HTML Import System** - Parse 100+ songs from mysongcollection.com format
✅ **Smart Metadata Extraction** - Automatically extracts tone sets, tempo, game types, and more
✅ **Powerful Search & Filter** - Find songs by tone set, game type, tempo, keywords, or free text
✅ **Repertoire Analytics** - View distribution charts and identify gaps in your collection
✅ **Song Detail Views** - Access full metadata, lyrics, directions, and notation references
✅ **CSV Export** - Backup your entire collection

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

Or use the startup script:
```bash
chmod +x start.sh
./start.sh
```

### 2. Start the Server

```bash
cd backend
python app.py
```

The application will be available at `http://localhost:5000`

### 3. Import Your Songs

1. Click on the **Import** tab
2. Click **"Drag & drop HTML files here"** or click to browse
3. Select one or more HTML files from your mysongcollection.com collection
4. Click **"Parse Files"**
5. Review the extracted data in the preview table
6. Click **"Save All to Database"**

That's it! Your songs are now in the system.

## Using RepSmith

### Browse & Search

1. Click the **Browse Songs** tab
2. Use the search box to find songs by title, lyrics, or keywords
3. Filter by:
   - **Tone Set** (e.g., "s-m", "d-r-m", "pentatonic")
   - **Game Type** (e.g., "circle game", "Play Party")
4. Click **Apply Filters** to search
5. Click **View** to see full song details
6. Sort by clicking column headers

### Dashboard Analytics

1. Click the **Dashboard** tab
2. View your collection statistics:
   - Total songs
   - Unique tone sets
   - Game type distribution
   - Tempo distribution
   - Top sources
3. Check the **Repertoire Gaps** section for areas that need more songs

### Export Your Collection

Click the **Export CSV** button in the header to download your entire collection as a CSV file.

## Supported HTML Format

RepSmith parses HTML files from mysongcollection.com with the following structure:

```html
<h2>Song Title</h2>
<table>
    <tr><td>S.S.P.:Eb</td><td align="RIGHT">circle game</td></tr>
    <tr><td>R.S.P.:Eb -F</td><td align="RIGHT">keywords, here</td></tr>
    <tr><td>l=120-136</td><td></td></tr>
    <tr><td>briskly</td><td align="RIGHT">s,l, (d)rm sl</td></tr>
</table>
```

### Extracted Fields

| Field | Pattern | Example |
|-------|---------|---------|
| Title | `<h2>` | "Chicken on the Fencepost" |
| Starting Pitch | `S.S.P.:` | "Eb", "c = sol" |
| Range | `R.S.P.:` | "Eb - F" |
| Tempo | `l=` or `I =` | "120-136", "96" |
| Character | 4th row left | "briskly", "gently" |
| Game Type | 1st row right | "circle game" |
| Keywords | 2nd row right | "chicken, dance, fencepost" |
| Tone Set | 3rd/4th row right | "(d)rmfsl", "s-m" |
| Meter | Notation table | "2/4", "6/8" |
| Directions | Text blocks | "Directions:", "Motions:" |

## Testing

Test files are included in the `tests/` directory:
- `test_chicken_fencepost.html` - Example with full metadata
- `test_tisket_tasket.html` - Example with missing character field
- `test_starlight.html` - Example with alternate title

You can use these to test the import functionality.

## Database

Songs are stored in SQLite database at `data/repsmith.db`

To reset the database:
```bash
rm data/repsmith.db
python backend/database.py
```

## Troubleshooting

### Parser Issues

If a song isn't parsing correctly:
1. Check that the HTML follows the expected format
2. Look at the **Warnings** column in the preview table
3. Manually edit fields before saving
4. Check the original HTML file structure

### Missing Fields

The parser handles missing fields gracefully:
- Missing **title** = Critical warning
- Missing **tone set** = Important warning
- Missing **character** = Normal (optional field)
- Missing **tempo** = Manual entry needed

### Search Not Working

Make sure you:
1. Saved songs to the database after import
2. Applied filters by clicking **Apply Filters**
3. Used correct search syntax (partial matches work)

## Next Steps

### Manual Entry Form (Planned)

A manual entry form for adding songs not in HTML format is planned for a future update.

### Collections (Available Now)

Create custom collections via the API:
```bash
curl -X POST http://localhost:5000/api/collections \
  -H "Content-Type: application/json" \
  -d '{"name": "Grade 2 Fall", "description": "Songs for Grade 2 Fall semester"}'
```

## Support

For issues or questions:
1. Check the console for error messages (F12 in browser)
2. Check the server logs in the terminal
3. Review test files for format examples

## Project Structure

```
repsmith/
├── backend/
│   ├── app.py          # Flask application
│   ├── models.py       # Database models
│   ├── parser.py       # HTML parser
│   └── database.py     # Database setup
├── frontend/
│   ├── templates/      # HTML templates
│   │   └── index.html  # Main UI
│   └── static/
│       └── js/
│           └── app.js  # Frontend JavaScript
├── tests/              # Test HTML files
├── uploads/            # Uploaded files
├── data/               # SQLite database
└── requirements.txt    # Python dependencies
```

## Success Criteria

✅ Import 100 HTML songs with 95%+ accuracy
✅ Parse both example formats correctly
✅ Find songs in under 10 seconds
✅ Access original notation via links
✅ Identify repertoire gaps

Happy teaching! 🎵
