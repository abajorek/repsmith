"""
Database models for RepSmith application.
"""
from sqlalchemy import create_engine, Column, Integer, String, Text, Float, DateTime, Table, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

# Association table for song collections
song_collections = Table('song_collections', Base.metadata,
    Column('song_id', Integer, ForeignKey('songs.id')),
    Column('collection_id', Integer, ForeignKey('collections.id'))
)


class Song(Base):
    """Main song entity with all metadata."""
    __tablename__ = 'songs'

    id = Column(Integer, primary_key=True)

    # Basic Information
    title = Column(String(200), nullable=False, index=True)
    alternate_titles = Column(String(500))

    # Musical Attributes
    tone_set = Column(String(100), index=True)  # e.g., "s-m", "d-r-m", "(d)rmfsl"
    range = Column(String(50))  # e.g., "Eb - F", "c = sol"
    starting_pitch = Column(String(50))  # S.S.P. - e.g., "Eb", "c = sol"
    meter = Column(String(20))  # e.g., "2/4", "6/8"
    tempo = Column(String(50))  # e.g., "120-136", "96"
    tempo_min = Column(Integer)  # Extracted min tempo for filtering
    tempo_max = Column(Integer)  # Extracted max tempo for filtering
    character = Column(String(100))  # e.g., "briskly", "gently"
    key_signature = Column(String(20))  # Concert pitch
    melodic_elements = Column(Text)  # Intervals, skips, leaps
    rhythmic_elements = Column(Text)  # Kodály syllables

    # Pedagogical Context
    teaching_purpose = Column(Text)  # e.g., "prepare s-m, present ta-ti"
    sequence_level = Column(String(50))  # beginner, intermediate, advanced
    cultural_origin = Column(String(100))  # Country/region
    game_type = Column(String(100), index=True)  # e.g., "circle game", "Play Party"
    source = Column(Text)  # Book/collection reference
    borrowed_from = Column(String(200))  # Original teacher/contributor

    # Content Fields
    lyrics = Column(Text)  # Extracted from notation table
    directions = Column(Text)  # Game instructions
    keywords = Column(String(500), index=True)  # e.g., "chicken, dance, fencepost"
    notes = Column(Text)  # Teacher observations
    notation_reference = Column(String(500))  # Path to original HTML file
    similar_songs = Column(Text)  # Comma-separated song IDs or titles

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    collections = relationship('Collection', secondary=song_collections, back_populates='songs')

    def to_dict(self):
        """Convert song to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'title': self.title,
            'alternate_titles': self.alternate_titles,
            'tone_set': self.tone_set,
            'range': self.range,
            'starting_pitch': self.starting_pitch,
            'meter': self.meter,
            'tempo': self.tempo,
            'tempo_min': self.tempo_min,
            'tempo_max': self.tempo_max,
            'character': self.character,
            'key_signature': self.key_signature,
            'melodic_elements': self.melodic_elements,
            'rhythmic_elements': self.rhythmic_elements,
            'teaching_purpose': self.teaching_purpose,
            'sequence_level': self.sequence_level,
            'cultural_origin': self.cultural_origin,
            'game_type': self.game_type,
            'source': self.source,
            'borrowed_from': self.borrowed_from,
            'lyrics': self.lyrics,
            'directions': self.directions,
            'keywords': self.keywords,
            'notes': self.notes,
            'notation_reference': self.notation_reference,
            'similar_songs': self.similar_songs,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class Collection(Base):
    """Custom song collections (e.g., 'Grade 2 Fall', 'Circle Games')."""
    __tablename__ = 'collections'

    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False, unique=True)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    songs = relationship('Song', secondary=song_collections, back_populates='collections')

    def to_dict(self):
        """Convert collection to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'song_count': len(self.songs),
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
