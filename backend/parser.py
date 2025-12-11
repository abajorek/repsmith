"""
HTML parser for mysongcollection.com format.

Handles structural variations while extracting all relevant metadata.
"""
import re
from bs4 import BeautifulSoup
from typing import Dict, Optional, List


class SongHTMLParser:
    """Parser for song HTML files from mysongcollection.com."""

    def __init__(self):
        self.warnings = []

    def parse_file(self, file_path: str) -> Dict:
        """Parse HTML file and extract song metadata."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                html_content = f.read()
            return self.parse_html(html_content, file_path)
        except Exception as e:
            return {
                'error': f"Failed to parse file: {str(e)}",
                'file_path': file_path
            }

    def parse_html(self, html_content: str, file_path: str = None) -> Dict:
        """Parse HTML content and extract song metadata."""
        self.warnings = []
        soup = BeautifulSoup(html_content, 'html.parser')

        song_data = {
            'notation_reference': file_path,
            'warnings': []
        }

        # 1. Extract title (required)
        song_data['title'] = self._extract_title(soup)
        if not song_data['title']:
            self.warnings.append("Missing title (critical)")

        # 2. Extract alternate title (optional)
        song_data['alternate_titles'] = self._extract_alternate_title(soup)

        # 3. Extract metadata from the main table
        metadata_table = self._find_metadata_table(soup)
        if metadata_table:
            self._extract_table_metadata(metadata_table, song_data)
        else:
            self.warnings.append("Metadata table not found")

        # 4. Extract tempo (handle both "l=" and "I =" patterns)
        tempo_info = self._extract_tempo(soup)
        song_data['tempo'] = tempo_info['tempo']
        song_data['tempo_min'] = tempo_info['tempo_min']
        song_data['tempo_max'] = tempo_info['tempo_max']

        # 5. Extract meter from notation table
        song_data['meter'] = self._extract_meter(soup)

        # 6. Extract directions (game instructions)
        song_data['directions'] = self._extract_directions(soup)

        # 7. Extract source and attribution
        source_info = self._extract_source_info(soup)
        song_data['source'] = source_info['source']
        song_data['borrowed_from'] = source_info['borrowed_from']

        # 8. Extract lyrics from notation table
        song_data['lyrics'] = self._extract_lyrics(soup)

        song_data['warnings'] = self.warnings
        return song_data

    def _extract_title(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract song title from <h2> tag."""
        title_tag = soup.find('h2')
        if title_tag:
            return title_tag.text.strip()
        return None

    def _extract_alternate_title(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract alternate title (text after </h2> before table)."""
        title_tag = soup.find('h2')
        if not title_tag:
            return None

        # Look for text immediately following the h2
        next_element = title_tag.next_sibling
        alternate_titles = []

        while next_element and next_element.name != 'table':
            if isinstance(next_element, str):
                text = next_element.strip()
                if text and text not in ['<br>', '<br/>', '']:
                    alternate_titles.append(text)
            elif next_element.name == 'br':
                pass
            else:
                text = next_element.get_text().strip()
                if text:
                    alternate_titles.append(text)
            next_element = next_element.next_sibling

        return ' '.join(alternate_titles) if alternate_titles else None

    def _find_metadata_table(self, soup: BeautifulSoup) -> Optional[BeautifulSoup]:
        """Find the metadata table containing S.S.P., R.S.P., etc."""
        tables = soup.find_all('table')

        for table in tables:
            # Look for table with S.S.P. or R.S.P.
            text = table.get_text()
            if 'S.S.P.' in text or 'R.S.P.' in text:
                return table

        return None

    def _extract_table_metadata(self, table: BeautifulSoup, song_data: Dict):
        """Extract metadata from the main metadata table."""
        rows = table.find_all('tr')

        for row in rows:
            cells = row.find_all('td')
            if not cells:
                continue

            # Extract left cell
            left_cell = cells[0].get_text().strip() if len(cells) > 0 else ""
            # Extract right cell (often right-aligned)
            right_cell = cells[-1].get_text().strip() if len(cells) > 1 else ""

            # Parse left cell
            if 'S.S.P.:' in left_cell:
                song_data['starting_pitch'] = left_cell.split('S.S.P.:')[1].strip()
            elif 'R.S.P.:' in left_cell:
                song_data['range'] = left_cell.split('R.S.P.:')[1].strip()
            elif re.search(r'[lI]\s*=\s*\d', left_cell):
                # Tempo is handled separately
                pass
            elif left_cell and not any(x in left_cell for x in ['S.S.P.', 'R.S.P.', '=']):
                # This might be the character field (e.g., "briskly")
                if 'character' not in song_data or not song_data['character']:
                    song_data['character'] = left_cell

            # Parse right cell
            # First row right cell is usually game type
            if right_cell and 'game_type' not in song_data:
                # Check if it looks like a game type
                game_keywords = ['game', 'play', 'party', 'dance', 'singing', 'circle']
                if any(keyword in right_cell.lower() for keyword in game_keywords):
                    song_data['game_type'] = right_cell
                    continue

            # Check if right cell contains keywords (comma-separated or single words)
            if right_cell and 'keywords' not in song_data:
                # Look for pattern that suggests keywords (lowercase, commas, or short phrases)
                if ',' in right_cell or (right_cell and len(right_cell) < 100 and not right_cell.startswith('(')):
                    # Check if it's not a tone set
                    if not re.match(r'[\(\)drmfsl,\s]+$', right_cell):
                        song_data['keywords'] = right_cell
                        continue

            # Check if right cell contains tone set
            if right_cell and 'tone_set' not in song_data:
                # Tone sets typically contain these characters
                if re.search(r'[\(\)drmfsl,\s]+', right_cell):
                    song_data['tone_set'] = right_cell

    def _extract_tempo(self, soup: BeautifulSoup) -> Dict:
        """Extract tempo from patterns like 'l=120-136' or 'I = 96'."""
        text = soup.get_text()

        # Try pattern 1: l=120-136
        match = re.search(r'l\s*=\s*([\d\-]+)', text, re.IGNORECASE)
        if not match:
            # Try pattern 2: I = 96
            match = re.search(r'I\s*=\s*([\d\-]+)', text)

        if match:
            tempo_str = match.group(1).strip()
            tempo_parts = tempo_str.split('-')

            try:
                tempo_min = int(tempo_parts[0])
                tempo_max = int(tempo_parts[-1])

                return {
                    'tempo': tempo_str,
                    'tempo_min': tempo_min,
                    'tempo_max': tempo_max
                }
            except ValueError:
                self.warnings.append(f"Could not parse tempo: {tempo_str}")
                return {'tempo': tempo_str, 'tempo_min': None, 'tempo_max': None}

        return {'tempo': None, 'tempo_min': None, 'tempo_max': None}

    def _extract_meter(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract meter (time signature) from notation table."""
        # Look for pattern: <font size="5">2<br>4</font>
        fonts = soup.find_all('font', size='5')

        for font in fonts:
            text = font.get_text()
            # Remove whitespace and look for number pattern
            text = text.strip().replace('\n', '').replace(' ', '')
            if re.match(r'\d+', text):
                # Check if there's a <br> tag
                if font.find('br'):
                    parts = font.get_text().strip().split('\n')
                    parts = [p.strip() for p in parts if p.strip()]
                    if len(parts) >= 2:
                        return f"{parts[0]}/{parts[1]}"

        # Alternative: look for explicit meter notation like "2/4" or "6/8"
        text = soup.get_text()
        match = re.search(r'\b(\d+/\d+)\b', text)
        if match:
            return match.group(1)

        return None

    def _extract_directions(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract game directions/motions."""
        text = soup.get_text()

        # Look for "Directions:" or "Motions:"
        patterns = [
            r'Directions?:\s*(.+?)(?=\n\n|\Z)',
            r'Motions?:\s*(.+?)(?=\n\n|\Z)'
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                directions = match.group(1).strip()
                # Clean up extra whitespace
                directions = re.sub(r'\s+', ' ', directions)
                return directions

        return None

    def _extract_source_info(self, soup: BeautifulSoup) -> Dict:
        """Extract source book and borrowed from attribution."""
        text = soup.get_text()

        source = None
        borrowed_from = None

        # Look for "Borrowed from:" pattern
        borrowed_match = re.search(r'Borrowed from:\s*([^\n]+)', text, re.IGNORECASE)
        if borrowed_match:
            borrowed_from = borrowed_match.group(1).strip()

        # Look for source before "Borrowed from:"
        # Common patterns: book titles, "from [book]", etc.
        if borrowed_from:
            # Get text before "Borrowed from:"
            before_borrowed = text.split('Borrowed from:')[0]
            # Look for book-like patterns (capitalized words, possibly with "from")
            source_match = re.search(r'(?:from\s+)?([A-Z][^.!?\n]{10,100}?)(?=\s*Borrowed from:)',
                                    before_borrowed, re.DOTALL)
            if source_match:
                source = source_match.group(1).strip()

        # Alternative: look for "Similar to:" pattern
        similar_match = re.search(r'Similar to:\s*([^\n]+)', text, re.IGNORECASE)
        if similar_match and not source:
            source = f"Similar to: {similar_match.group(1).strip()}"

        return {
            'source': source,
            'borrowed_from': borrowed_from
        }

    def _extract_lyrics(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract lyrics from notation table."""
        # This is complex as lyrics are embedded in the notation table
        # For now, we'll extract all text from tables that contain musical notation
        # and filter out metadata

        tables = soup.find_all('table')
        lyrics_parts = []

        for table in tables:
            text = table.get_text()
            # Skip metadata table
            if 'S.S.P.' in text or 'R.S.P.' in text:
                continue

            # Extract text that looks like lyrics (not notation)
            lines = text.split('\n')
            for line in lines:
                line = line.strip()
                # Filter out lines that are clearly not lyrics
                if line and len(line) > 2 and not re.match(r'^[\d\s/]+$', line):
                    # Skip tempo, key signatures, etc.
                    if not any(x in line for x in ['S.S.P.', 'R.S.P.', 'Borrowed', 'Directions']):
                        lyrics_parts.append(line)

        if lyrics_parts:
            return '\n'.join(lyrics_parts)

        return None


def parse_song_file(file_path: str) -> Dict:
    """Convenience function to parse a single song file."""
    parser = SongHTMLParser()
    return parser.parse_file(file_path)


def parse_song_batch(file_paths: List[str]) -> List[Dict]:
    """Parse multiple song files."""
    parser = SongHTMLParser()
    results = []

    for file_path in file_paths:
        result = parser.parse_file(file_path)
        results.append(result)

    return results


# Test with example HTML
if __name__ == '__main__':
    # Test HTML for "Chicken on the Fencepost"
    test_html_1 = """
    <html>
    <h2>Chicken on the Fencepost</h2>
    <table>
    <tr><td>S.S.P.:Eb</td><td align="RIGHT">circle game</td></tr>
    <tr><td>R.S.P.:Eb -F</td><td align="RIGHT">chicken, dance, fencepost</td></tr>
    <tr><td>l=120-136</td><td></td></tr>
    <tr><td>briskly</td><td align="RIGHT">s,l, (d)rm sl</td></tr>
    </table>
    </html>
    """

    # Test HTML for "A Tisket, A Tasket"
    test_html_2 = """
    <html>
    <h2>A Tisket, A Tasket</h2>
    <table>
    <tr><td>S.S.P.:c = sol</td><td align="RIGHT">Play Party</td></tr>
    <tr><td>R.S.P.:c = sol</td><td align="RIGHT">Love</td></tr>
    <tr><td>I = 96</td><td></td></tr>
    <tr><td></td><td align="RIGHT">(d)rmfsl</td></tr>
    </table>
    </html>
    """

    parser = SongHTMLParser()

    print("=" * 60)
    print("TEST 1: Chicken on the Fencepost")
    print("=" * 60)
    result1 = parser.parse_html(test_html_1)
    for key, value in result1.items():
        if value:
            print(f"{key}: {value}")

    print("\n" + "=" * 60)
    print("TEST 2: A Tisket, A Tasket")
    print("=" * 60)
    result2 = parser.parse_html(test_html_2)
    for key, value in result2.items():
        if value:
            print(f"{key}: {value}")
