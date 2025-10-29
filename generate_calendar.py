#!/usr/bin/env python3
"""
Generate an HTML calendar visualization of hut reservations.

Usage:
    python3 generate_calendar.py <allocation_csv> --output <output_html>
"""

import csv
import argparse
import calendar
from datetime import datetime, timedelta
from collections import defaultdict

# Color scheme for huts
HUT_COLORS = {
    'Bradley': '#FF6B6B',      # Red
    'Benson': '#4ECDC4',       # Teal
    'Peter Grubb': '#45B7D1',  # Blue
    'Ludlow': '#96CEB4'        # Green
}

def load_reservations(csv_file):
    """Load reservations from allocation CSV."""
    reservations = []

    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['Status'].startswith('ASSIGNED'):
                reservations.append({
                    'user': row['UserName'],
                    'hut': row['Hut'],
                    'start': datetime.strptime(row['StartDate'], '%Y-%m-%d'),
                    'end': datetime.strptime(row['EndDate'], '%Y-%m-%d'),
                    'party_size': row['PartySize'],
                    'traverse_group': row.get('TraverseGroup', '')
                })

    return reservations

def get_date_range(start_date, end_date):
    """Get all dates in a range (exclusive of end_date for overnight stays)."""
    dates = []
    current = start_date
    while current < end_date:
        dates.append(current)
        current += timedelta(days=1)
    return dates

def build_occupancy_map(reservations):
    """Build a map of date -> hut -> list of reservations."""
    occupancy = defaultdict(lambda: defaultdict(list))

    for res in reservations:
        dates = get_date_range(res['start'], res['end'])
        for date in dates:
            occupancy[date][res['hut']].append(res)

    return occupancy

def generate_month_html(year, month, occupancy, huts):
    """Generate HTML for a single month."""
    # Set first weekday to Sunday (US convention)
    calendar.setfirstweekday(calendar.SUNDAY)
    cal = calendar.monthcalendar(year, month)
    month_name = calendar.month_name[month]

    html = f'''
    <div class="month">
        <h2>{month_name} {year}</h2>
        <table class="calendar-table">
            <thead>
                <tr>
                    <th>Sun</th>
                    <th>Mon</th>
                    <th>Tue</th>
                    <th>Wed</th>
                    <th>Thu</th>
                    <th>Fri</th>
                    <th>Sat</th>
                </tr>
            </thead>
            <tbody>
    '''

    for week in cal:
        html += '<tr>'
        for day_index, day in enumerate(week):
            if day == 0:
                html += '<td class="empty"></td>'
            else:
                date = datetime(year, month, day)

                # Verify day of week matches (0=Monday, 6=Sunday in datetime)
                # calendar.monthcalendar uses 0=Monday, so we need to adjust
                actual_weekday = date.weekday()  # 0=Mon, 6=Sun
                # Convert to calendar format: 0=Sun, 6=Sat
                calendar_weekday = (actual_weekday + 1) % 7

                # Get day abbreviation for display
                day_abbrev = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'][day_index]

                html += f'<td class="day">'
                html += f'<div class="day-number">{day} <span class="day-abbrev">{day_abbrev}</span></div>'

                # Check each hut for reservations on this date
                for hut in huts:
                    if date in occupancy and hut in occupancy[date]:
                        color = HUT_COLORS.get(hut, '#999')
                        reservations = occupancy[date][hut]

                        # Calculate total occupancy
                        total_occupancy = sum(int(r['party_size']) for r in reservations)

                        # Show all users for this hut on this date
                        users = ', '.join(r['user'] for r in reservations)
                        traverse_info = ''
                        if reservations[0]['traverse_group']:
                            traverse_info = ' 🥾'

                        html += f'''
                        <div class="reservation" style="background-color: {color}; border-left: 4px solid {color};">
                            <div class="hut-name">{hut}{traverse_info}</div>
                            <div class="user-info">{users}</div>
                            <div class="occupancy">({total_occupancy} people)</div>
                        </div>
                        '''

                html += '</td>'
        html += '</tr>\n'

    html += '''
            </tbody>
        </table>
    </div>
    '''

    return html

def verify_calendar_alignment(year, month):
    """Verify that calendar days align with correct weekdays."""
    print(f"\nVerifying {calendar.month_name[month]} {year}:")
    # Set first weekday to Sunday to match table headers
    calendar.setfirstweekday(calendar.SUNDAY)
    cal = calendar.monthcalendar(year, month)
    day_names = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']

    for week in cal[:2]:  # Just check first 2 weeks
        for day_index, day in enumerate(week):
            if day != 0:
                date = datetime(year, month, day)
                actual_weekday = date.strftime('%a')
                expected_weekday = day_names[day_index]
                match = "✓" if actual_weekday == expected_weekday else "✗"
                print(f"  {match} Day {day}: Column={expected_weekday}, Actual={actual_weekday}")

def generate_html_calendar(reservations, output_file, season_start, season_end):
    """Generate complete HTML calendar."""
    huts = ['Bradley', 'Benson', 'Peter Grubb', 'Ludlow']
    occupancy = build_occupancy_map(reservations)

    # Verify alignment for first month
    verify_calendar_alignment(season_start.year, season_start.month)

    # Generate legend
    legend_html = '<div class="legend"><h3>Huts:</h3>'
    for hut, color in HUT_COLORS.items():
        legend_html += f'<div class="legend-item"><span class="color-box" style="background-color: {color};"></span> {hut}</div>'
    legend_html += '<div class="legend-item">🥾 = Traverse</div>'
    legend_html += '</div>'

    # Build HTML
    html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Backcountry Hut Reservations Calendar</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}

        h1 {{
            text-align: center;
            color: #333;
            margin-bottom: 10px;
        }}

        .subtitle {{
            text-align: center;
            color: #666;
            margin-bottom: 30px;
            font-size: 14px;
        }}

        .legend {{
            background: white;
            padding: 15px;
            margin-bottom: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 20px;
            flex-wrap: wrap;
        }}

        .legend h3 {{
            margin: 0;
            font-size: 16px;
        }}

        .legend-item {{
            display: flex;
            align-items: center;
            gap: 8px;
        }}

        .color-box {{
            width: 20px;
            height: 20px;
            border-radius: 3px;
            display: inline-block;
        }}

        .calendar-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(600px, 1fr));
            gap: 20px;
        }}

        .month {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}

        .month h2 {{
            margin-top: 0;
            color: #333;
            font-size: 20px;
            border-bottom: 2px solid #e0e0e0;
            padding-bottom: 10px;
        }}

        .calendar-table {{
            width: 100%;
            border-collapse: collapse;
        }}

        .calendar-table th {{
            padding: 8px;
            text-align: center;
            font-size: 12px;
            color: #666;
            font-weight: 600;
            border-bottom: 2px solid #e0e0e0;
        }}

        .calendar-table td {{
            border: 1px solid #e0e0e0;
            vertical-align: top;
            height: 120px;
            padding: 4px;
            position: relative;
        }}

        .calendar-table td.empty {{
            background-color: #fafafa;
        }}

        .day-number {{
            font-size: 14px;
            font-weight: 600;
            color: #333;
            margin-bottom: 4px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        .day-abbrev {{
            font-size: 10px;
            color: #999;
            font-weight: 400;
        }}

        .reservation {{
            font-size: 10px;
            padding: 4px;
            margin: 2px 0;
            border-radius: 3px;
            background-color: #f0f0f0;
            overflow: hidden;
        }}

        .hut-name {{
            font-weight: 600;
            margin-bottom: 2px;
        }}

        .user-info {{
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}

        .occupancy {{
            font-size: 9px;
            color: #666;
            font-style: italic;
        }}

        @media print {{
            body {{
                background: white;
            }}
            .month {{
                page-break-inside: avoid;
                box-shadow: none;
            }}
        }}
    </style>
</head>
<body>
    <h1>🏔️ Backcountry Hut Reservations Calendar</h1>
    <div class="subtitle">Season {season_start.strftime('%B %d, %Y')} - {season_end.strftime('%B %d, %Y')}</div>

    {legend_html}

    <div class="calendar-grid">
'''

    # Generate each month in the season
    current = season_start
    while current <= season_end:
        html += generate_month_html(current.year, current.month, occupancy, huts)

        # Move to next month
        if current.month == 12:
            current = datetime(current.year + 1, 1, 1)
        else:
            current = datetime(current.year, current.month + 1, 1)

    html += '''
    </div>
</body>
</html>
'''

    with open(output_file, 'w') as f:
        f.write(html)

    print(f"Calendar generated: {output_file}")

def main():
    parser = argparse.ArgumentParser(description='Generate HTML calendar from allocation results')
    parser.add_argument('allocation_csv', help='Path to allocation CSV file')
    parser.add_argument('--output', '-o', default='calendar.html', help='Output HTML file')
    parser.add_argument('--start', default='2025-12-01', help='Season start date (YYYY-MM-DD)')
    parser.add_argument('--end', default='2026-05-31', help='Season end date (YYYY-MM-DD)')

    args = parser.parse_args()

    # Load reservations
    reservations = load_reservations(args.allocation_csv)
    print(f"Loaded {len(reservations)} reservations from {args.allocation_csv}")

    # Parse season dates
    season_start = datetime.strptime(args.start, '%Y-%m-%d')
    season_end = datetime.strptime(args.end, '%Y-%m-%d')

    # Generate calendar
    generate_html_calendar(reservations, args.output, season_start, season_end)

if __name__ == '__main__':
    main()
