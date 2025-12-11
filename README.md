# RepSmith - Kodály Repertoire Analysis Tool

A web-based repertoire management system for Kodály-inspired music educators.

## Features

- Import songs from HTML files (mysongcollection.com format)
- Catalog with detailed pedagogical metadata
- Powerful search and filter capabilities
- Repertoire gap analysis
- Dashboard with analytics

## Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python backend/app.py
```

## Usage

1. Navigate to http://localhost:5000
2. Upload HTML files from mysongcollection.com
3. Preview and edit extracted metadata
4. Save songs to database
5. Search, filter, and analyze your repertoire

## Project Structure

```
repsmith/
├── backend/           # Flask application
│   ├── app.py        # Main application
│   ├── models.py     # Database models
│   ├── parser.py     # HTML parser
│   └── database.py   # Database setup
├── frontend/         # Web interface
│   ├── templates/    # HTML templates
│   └── static/       # CSS/JS files
├── tests/            # Test files
├── uploads/          # Uploaded HTML files
└── data/             # SQLite database
```
