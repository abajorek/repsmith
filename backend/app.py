"""
RepSmith Flask Application - Kodály Repertoire Analysis Tool
"""
import os
import json
from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
from sqlalchemy import or_, and_
from datetime import datetime

from database import init_db, SessionLocal, DATABASE_PATH
from models import Song, Collection
from parser import SongHTMLParser

app = Flask(__name__,
            template_folder='../frontend/templates',
            static_folder='../frontend/static')
CORS(app)

# Configuration
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
ALLOWED_EXTENSIONS = {'html', 'htm'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize database
init_db()


def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    """Home page."""
    return render_template('index.html')


@app.route('/notation/<path:filename>')
def serve_notation(filename):
    """Serve uploaded HTML notation files."""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/api/upload', methods=['POST'])
def upload_files():
    """
    Upload and parse HTML files.
    Returns parsed song data for preview.
    """
    if 'files[]' not in request.files:
        return jsonify({'error': 'No files provided'}), 400

    files = request.files.getlist('files[]')
    if not files:
        return jsonify({'error': 'No files selected'}), 400

    parser = SongHTMLParser()
    parsed_songs = []
    errors = []

    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            # Parse the file
            try:
                song_data = parser.parse_file(filepath)
                song_data['filename'] = filename
                song_data['filepath'] = filepath
                # Store just filename for notation reference (for serving via /notation/<filename>)
                song_data['notation_reference'] = filename
                parsed_songs.append(song_data)
            except Exception as e:
                errors.append({
                    'filename': filename,
                    'error': str(e)
                })
        else:
            errors.append({
                'filename': file.filename,
                'error': 'Invalid file type. Only HTML files allowed.'
            })

    return jsonify({
        'parsed_songs': parsed_songs,
        'errors': errors,
        'total': len(parsed_songs)
    })


@app.route('/api/songs', methods=['GET', 'POST'])
def songs():
    """
    GET: List all songs with optional filtering
    POST: Create new song(s) from parsed data
    """
    db = SessionLocal()

    try:
        if request.method == 'POST':
            # Create new songs
            data = request.json
            songs_data = data.get('songs', [])

            if not songs_data:
                return jsonify({'error': 'No song data provided'}), 400

            created_songs = []
            for song_data in songs_data:
                # Remove warnings and other non-model fields
                song_data.pop('warnings', None)
                song_data.pop('filename', None)
                song_data.pop('filepath', None)

                song = Song(**song_data)
                db.add(song)
                created_songs.append(song)

            db.commit()

            return jsonify({
                'message': f'Successfully created {len(created_songs)} songs',
                'songs': [song.to_dict() for song in created_songs]
            }), 201

        else:
            # GET: List songs with filtering
            query = db.query(Song)

            # Apply filters
            tone_set = request.args.get('tone_set')
            if tone_set:
                query = query.filter(Song.tone_set.like(f'%{tone_set}%'))

            game_type = request.args.get('game_type')
            if game_type:
                query = query.filter(Song.game_type.like(f'%{game_type}%'))

            keywords = request.args.get('keywords')
            if keywords:
                query = query.filter(Song.keywords.like(f'%{keywords}%'))

            tempo_min = request.args.get('tempo_min')
            tempo_max = request.args.get('tempo_max')
            if tempo_min:
                query = query.filter(Song.tempo_min >= int(tempo_min))
            if tempo_max:
                query = query.filter(Song.tempo_max <= int(tempo_max))

            search = request.args.get('search')
            if search:
                search_pattern = f'%{search}%'
                query = query.filter(
                    or_(
                        Song.title.like(search_pattern),
                        Song.lyrics.like(search_pattern),
                        Song.directions.like(search_pattern),
                        Song.keywords.like(search_pattern)
                    )
                )

            # Sorting
            sort_by = request.args.get('sort_by', 'title')
            sort_order = request.args.get('sort_order', 'asc')

            if hasattr(Song, sort_by):
                column = getattr(Song, sort_by)
                if sort_order == 'desc':
                    query = query.order_by(column.desc())
                else:
                    query = query.order_by(column.asc())

            # Pagination
            page = int(request.args.get('page', 1))
            per_page = int(request.args.get('per_page', 20))

            total = query.count()
            songs = query.offset((page - 1) * per_page).limit(per_page).all()

            return jsonify({
                'songs': [song.to_dict() for song in songs],
                'total': total,
                'page': page,
                'per_page': per_page,
                'pages': (total + per_page - 1) // per_page
            })

    finally:
        db.close()


@app.route('/api/songs/<int:song_id>', methods=['GET', 'PUT', 'DELETE'])
def song_detail(song_id):
    """Get, update, or delete a specific song."""
    db = SessionLocal()

    try:
        song = db.query(Song).filter(Song.id == song_id).first()
        if not song:
            return jsonify({'error': 'Song not found'}), 404

        if request.method == 'GET':
            return jsonify(song.to_dict())

        elif request.method == 'PUT':
            # Update song
            data = request.json
            for key, value in data.items():
                if hasattr(song, key):
                    setattr(song, key, value)

            song.updated_at = datetime.utcnow()
            db.commit()

            return jsonify({
                'message': 'Song updated successfully',
                'song': song.to_dict()
            })

        elif request.method == 'DELETE':
            db.delete(song)
            db.commit()
            return jsonify({'message': 'Song deleted successfully'})

    finally:
        db.close()


@app.route('/api/songs/search', methods=['GET'])
def search_songs():
    """Advanced search endpoint."""
    db = SessionLocal()

    try:
        query = db.query(Song)

        # Build complex query from parameters
        filters = []

        # Text search
        q = request.args.get('q')
        if q:
            search_pattern = f'%{q}%'
            filters.append(
                or_(
                    Song.title.like(search_pattern),
                    Song.alternate_titles.like(search_pattern),
                    Song.lyrics.like(search_pattern),
                    Song.keywords.like(search_pattern)
                )
            )

        # Apply filters
        if filters:
            query = query.filter(and_(*filters))

        songs = query.all()
        return jsonify({
            'songs': [song.to_dict() for song in songs],
            'count': len(songs)
        })

    finally:
        db.close()


@app.route('/api/analytics/dashboard', methods=['GET'])
def analytics_dashboard():
    """Get analytics data for dashboard."""
    db = SessionLocal()

    try:
        # Total songs
        total_songs = db.query(Song).count()

        # Tone set distribution
        tone_sets = db.query(Song.tone_set, db.func.count(Song.id))\
            .filter(Song.tone_set.isnot(None))\
            .group_by(Song.tone_set)\
            .all()
        tone_set_dist = [{'tone_set': ts, 'count': count} for ts, count in tone_sets]

        # Game type distribution
        game_types = db.query(Song.game_type, db.func.count(Song.id))\
            .filter(Song.game_type.isnot(None))\
            .group_by(Song.game_type)\
            .all()
        game_type_dist = [{'game_type': gt, 'count': count} for gt, count in game_types]

        # Tempo distribution (group by ranges)
        tempo_ranges = [
            (0, 80, 'Very Slow'),
            (80, 100, 'Slow'),
            (100, 120, 'Moderate'),
            (120, 140, 'Fast'),
            (140, 200, 'Very Fast')
        ]

        tempo_dist = []
        for min_tempo, max_tempo, label in tempo_ranges:
            count = db.query(Song).filter(
                and_(
                    Song.tempo_min >= min_tempo,
                    Song.tempo_min < max_tempo
                )
            ).count()
            tempo_dist.append({
                'range': label,
                'min': min_tempo,
                'max': max_tempo,
                'count': count
            })

        # Most represented sources
        sources = db.query(Song.source, db.func.count(Song.id))\
            .filter(Song.source.isnot(None))\
            .group_by(Song.source)\
            .order_by(db.func.count(Song.id).desc())\
            .limit(10)\
            .all()
        source_dist = [{'source': src, 'count': count} for src, count in sources]

        return jsonify({
            'total_songs': total_songs,
            'tone_set_distribution': tone_set_dist,
            'game_type_distribution': game_type_dist,
            'tempo_distribution': tempo_dist,
            'source_distribution': source_dist
        })

    finally:
        db.close()


@app.route('/api/collections', methods=['GET', 'POST'])
def collections():
    """List or create collections."""
    db = SessionLocal()

    try:
        if request.method == 'POST':
            data = request.json
            collection = Collection(
                name=data['name'],
                description=data.get('description')
            )
            db.add(collection)
            db.commit()

            return jsonify({
                'message': 'Collection created successfully',
                'collection': collection.to_dict()
            }), 201
        else:
            collections = db.query(Collection).all()
            return jsonify({
                'collections': [c.to_dict() for c in collections]
            })

    finally:
        db.close()


@app.route('/api/collections/<int:collection_id>/songs', methods=['POST', 'DELETE'])
def collection_songs(collection_id):
    """Add or remove songs from a collection."""
    db = SessionLocal()

    try:
        collection = db.query(Collection).filter(Collection.id == collection_id).first()
        if not collection:
            return jsonify({'error': 'Collection not found'}), 404

        song_id = request.json.get('song_id')
        song = db.query(Song).filter(Song.id == song_id).first()
        if not song:
            return jsonify({'error': 'Song not found'}), 404

        if request.method == 'POST':
            if song not in collection.songs:
                collection.songs.append(song)
                db.commit()
            return jsonify({'message': 'Song added to collection'})
        else:
            if song in collection.songs:
                collection.songs.remove(song)
                db.commit()
            return jsonify({'message': 'Song removed from collection'})

    finally:
        db.close()


@app.route('/api/export/csv', methods=['GET'])
def export_csv():
    """Export songs as CSV."""
    db = SessionLocal()

    try:
        songs = db.query(Song).all()

        # Create CSV content
        import csv
        import io

        output = io.StringIO()
        writer = csv.writer(output)

        # Header
        headers = ['Title', 'Tone Set', 'Range', 'Starting Pitch', 'Meter', 'Tempo',
                   'Game Type', 'Keywords', 'Character', 'Source', 'Borrowed From']
        writer.writerow(headers)

        # Data rows
        for song in songs:
            writer.writerow([
                song.title,
                song.tone_set,
                song.range,
                song.starting_pitch,
                song.meter,
                song.tempo,
                song.game_type,
                song.keywords,
                song.character,
                song.source,
                song.borrowed_from
            ])

        output.seek(0)

        from flask import Response
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': 'attachment; filename=repsmith_export.csv'}
        )

    finally:
        db.close()


if __name__ == '__main__':
    print(f"Database: {DATABASE_PATH}")
    print("Starting RepSmith server on http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
