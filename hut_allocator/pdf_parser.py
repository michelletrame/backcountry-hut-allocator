"""
PDF Parser for extracting reservation requests from PDF forms.
"""
import pdfplumber
import re
from datetime import datetime

class PDFParser:
    """Parse reservation request data from PDF forms."""

    def __init__(self, pdf_path):
        self.pdf_path = pdf_path
        self.text = ""
        self.data = {
            'leader_name': None,
            'email': None,
            'phone': None,
            'preferences': []
        }

    def extract_text(self):
        """Extract all text from PDF."""
        with pdfplumber.open(self.pdf_path) as pdf:
            for page in pdf.pages:
                self.text += page.extract_text() + "\n"
        return self.text

    def parse(self):
        """
        Parse the PDF and extract structured data.
        Returns dict with leader info and preferences.
        """
        self.extract_text()

        # Extract leader information
        self._extract_leader_info()

        # Extract preferences
        self._extract_preferences()

        return self.data

    def _extract_leader_info(self):
        """Extract leader name, email, and phone from text."""
        lines = self.text.split('\n')

        # Look for patterns
        for i, line in enumerate(lines):
            # Email pattern
            email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', line)
            if email_match:
                self.data['email'] = email_match.group()

            # Phone pattern (various formats)
            phone_match = re.search(r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b', line)
            if phone_match:
                self.data['phone'] = phone_match.group()

            # Leader name (usually appears after "Leader Name" or at the top)
            if 'Leader Name' in line and i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if next_line and 'Email' not in next_line:
                    self.data['leader_name'] = next_line

    def _extract_preferences(self):
        """Extract hut preferences from text."""
        lines = self.text.split('\n')

        current_pref = None
        pref_data = {}

        for i, line in enumerate(lines):
            line = line.strip()

            # Detect preference headers
            pref_match = re.match(r'Hut Preference #(\d)', line)
            if pref_match:
                # Save previous preference if exists
                if current_pref and self._is_valid_preference(pref_data):
                    self.data['preferences'].append(pref_data)

                # Start new preference
                current_pref = int(pref_match.group(1))
                pref_data = {'preference_rank': current_pref}
                continue

            # Skip if not in a preference section
            if current_pref is None:
                continue

            # Extract data based on field names
            if 'Hut Name' in line and i + 1 < len(lines):
                hut_name = lines[i + 1].strip()
                if hut_name and 'Date' not in hut_name:
                    pref_data['hut_name'] = hut_name

            elif 'Date In' in line and i + 1 < len(lines):
                date_in = lines[i + 1].strip()
                if date_in and self._looks_like_date(date_in):
                    pref_data['date_in'] = self._parse_date(date_in)

            elif 'Date Out' in line and i + 1 < len(lines):
                date_out = lines[i + 1].strip()
                if date_out and self._looks_like_date(date_out):
                    pref_data['date_out'] = self._parse_date(date_out)

            elif 'Number of Guests' in line and i + 1 < len(lines):
                guests = lines[i + 1].strip()
                if guests and guests.upper() != 'ENTIRE':
                    try:
                        pref_data['party_size'] = int(re.search(r'\d+', guests).group())
                    except:
                        pass
                elif guests.upper() == 'ENTIRE':
                    pref_data['party_size'] = 'ENTIRE'

        # Don't forget the last preference
        if current_pref and self._is_valid_preference(pref_data):
            self.data['preferences'].append(pref_data)

    def _looks_like_date(self, text):
        """Check if text looks like a date."""
        # Common date patterns
        patterns = [
            r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}',
            r'\d{4}[/-]\d{1,2}[/-]\d{1,2}',
            r'[A-Za-z]{3,}\s+\d{1,2},?\s+\d{4}',
        ]
        for pattern in patterns:
            if re.search(pattern, text):
                return True
        return False

    def _parse_date(self, date_str):
        """Parse various date formats."""
        # Try common formats
        formats = [
            '%m/%d/%Y',
            '%m-%d-%Y',
            '%Y-%m-%d',
            '%m/%d/%y',
            '%m-%d-%y',
            '%B %d, %Y',
            '%b %d, %Y',
            '%B %d %Y',
            '%b %d %Y',
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str.strip(), fmt).strftime('%Y-%m-%d')
            except:
                continue

        # If no format works, return original
        return date_str

    def _is_valid_preference(self, pref_data):
        """Check if preference has minimum required data."""
        required = ['preference_rank', 'hut_name', 'date_in', 'date_out', 'party_size']
        return all(key in pref_data for key in required)

    def to_csv_rows(self):
        """Convert parsed data to CSV row format."""
        rows = []
        leader_name = self.data.get('leader_name', 'Unknown')

        for pref in self.data['preferences']:
            rows.append({
                'UserName': leader_name,
                'PreferenceRank': pref['preference_rank'],
                'Hut': pref['hut_name'],
                'StartDate': pref['date_in'],
                'EndDate': pref['date_out'],
                'PartySize': pref['party_size']
            })

        return rows
