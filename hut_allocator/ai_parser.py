"""
AI-powered parser using Claude API for handling complex or handwritten forms.
"""
import os
import base64
import json
from anthropic import Anthropic

class AIParser:
    """Use Claude AI to extract reservation data from documents."""

    def __init__(self, file_path, api_key=None):
        self.file_path = file_path
        self.api_key = api_key or os.environ.get('ANTHROPIC_API_KEY')
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not found. Set it as environment variable or pass it directly.")
        self.client = Anthropic(api_key=self.api_key)

    def parse(self):
        """
        Use Claude to parse the document and extract structured data.
        Returns dict with leader info and preferences.
        """
        # Read and encode the file
        with open(self.file_path, 'rb') as f:
            file_data = base64.standard_b64encode(f.read()).decode('utf-8')

        # Determine media type
        file_ext = self.file_path.lower().split('.')[-1]
        media_type_map = {
            'pdf': 'application/pdf',
            'png': 'image/png',
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
        }
        media_type = media_type_map.get(file_ext, 'application/pdf')

        # Create the prompt
        prompt = """
Please extract reservation request information from this form.

The form contains:
1. Leader Contact Information (Leader Name, Email, Phone)
2. Up to 5 Hut Preferences, each with:
   - Hut Name
   - Date In
   - Date Out
   - Number of Guests (or "ENTIRE" for exclusive use)

Return the data as a JSON object with this structure:
{
    "leader_name": "Full Name",
    "email": "email@example.com",
    "phone": "555-123-4567",
    "preferences": [
        {
            "preference_rank": 1,
            "hut_name": "Hut Name",
            "date_in": "2026-02-12",
            "date_out": "2026-02-14",
            "party_size": 4
        }
    ]
}

Important:
- Format dates as YYYY-MM-DD
- Only include preferences that have all required fields filled out
- If a field is blank or unclear, omit that preference
- party_size should be a number, or the string "ENTIRE" if specified
- Preserve the exact preference ranking (1-5) as shown in the form

Return ONLY the JSON object, no other text.
"""

        try:
            # Call Claude API
            message = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=2048,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "document",
                                "source": {
                                    "type": "base64",
                                    "media_type": media_type,
                                    "data": file_data
                                }
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                ]
            )

            # Extract the response
            response_text = message.content[0].text

            # Parse JSON from response
            # Claude might wrap it in markdown code blocks, so clean it
            response_text = response_text.strip()
            if response_text.startswith('```'):
                # Remove markdown code blocks
                lines = response_text.split('\n')
                response_text = '\n'.join(lines[1:-1])
            if response_text.startswith('json'):
                response_text = response_text[4:].strip()

            data = json.loads(response_text)
            return data

        except Exception as e:
            print(f"AI parsing error: {e}")
            return {
                'leader_name': None,
                'email': None,
                'phone': None,
                'preferences': [],
                'error': str(e)
            }

    def to_csv_rows(self):
        """Convert parsed data to CSV row format."""
        data = self.parse()
        rows = []
        leader_name = data.get('leader_name', 'Unknown')

        for pref in data.get('preferences', []):
            rows.append({
                'UserName': leader_name,
                'PreferenceRank': pref['preference_rank'],
                'Hut': pref['hut_name'],
                'StartDate': pref['date_in'],
                'EndDate': pref['date_out'],
                'PartySize': pref['party_size']
            })

        return rows
