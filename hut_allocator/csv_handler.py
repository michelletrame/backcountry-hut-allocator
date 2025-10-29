import csv
from datetime import datetime
from hut_allocator.reservation_request import ReservationRequest

def load_requests_from_csv(filename):
    """
    Load reservation requests from CSV file.

    Expected CSV format:
    UserName,PreferenceRank,Hut,StartDate,EndDate,PartySize,TraverseGroup

    Example:
    John Smith,1,Bradley,2026-02-12,2026-02-14,4,
    John Smith,2,Benson,2026-02-15,2026-02-17,ENTIRE,
    Jane Doe,3,Bradley,2026-03-20,2026-03-22,4,traverse_1
    Jane Doe,3,Benson,2026-03-22,2026-03-23,4,traverse_1
    """
    from hut_allocator.config import HUTS

    requests = []

    with open(filename, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Handle ENTIRE party size
            party_size_str = row['PartySize'].strip()
            hut_name = row['Hut'].strip()

            if party_size_str.upper() == 'ENTIRE':
                # Get hut capacity
                party_size = HUTS.get(hut_name, 15)  # Default to 15 if hut not found
            else:
                party_size = int(party_size_str)

            # Get traverse group (optional field for backward compatibility)
            traverse_group = row.get('TraverseGroup', '').strip() or None

            # Get sanctioned status (optional field for backward compatibility)
            sanctioned_value = row.get('Sanctioned', '').strip().upper()
            sanctioned = sanctioned_value in ['YES', 'TRUE', '1']

            request = ReservationRequest(
                user_name=row['UserName'].strip(),
                preference_rank=int(row['PreferenceRank']),
                hut_name=hut_name,
                start_date=row['StartDate'].strip(),
                end_date=row['EndDate'].strip(),
                party_size=party_size,
                traverse_group=traverse_group,
                sanctioned=sanctioned
            )
            requests.append(request)

    return requests

def save_allocation_to_csv(allocation, filename):
    """
    Save allocation results to CSV file.

    Output format:
    UserName,PreferenceRank,Hut,StartDate,EndDate,PartySize,TraverseGroup,Sanctioned,Status
    """
    with open(filename, 'w', newline='') as f:
        fieldnames = ['UserName', 'PreferenceRank', 'Hut', 'StartDate', 'EndDate', 'PartySize', 'TraverseGroup', 'Sanctioned', 'Status']
        writer = csv.DictWriter(f, fieldnames=fieldnames)

        writer.writeheader()

        # Get all users
        users = set(req.user_name for req in allocation.requests)

        for user in sorted(users):
            user_requests = allocation.get_user_requests(user)

            # Find assigned request(s) - could be multiple for traverses
            assigned = [req for req in user_requests if req.assigned]

            if assigned:
                # Sort by traverse group, then start date to keep traverse legs together
                assigned_sorted = sorted(assigned, key=lambda r: (r.traverse_group or '', r.start_date))

                for req in assigned_sorted:
                    writer.writerow({
                        'UserName': req.user_name,
                        'PreferenceRank': req.preference_rank,
                        'Hut': req.hut_name,
                        'StartDate': req.start_date.strftime('%Y-%m-%d'),
                        'EndDate': req.end_date.strftime('%Y-%m-%d'),
                        'PartySize': req.party_size,
                        'TraverseGroup': req.traverse_group or '',
                        'Sanctioned': 'YES' if req.is_sanctioned else '',
                        'Status': f'ASSIGNED (Preference {req.preference_rank})' + (' [SANCTIONED]' if req.is_sanctioned else '')
                    })
            else:
                # List all unassigned requests for this user
                for req in sorted(user_requests, key=lambda r: (r.preference_rank, r.start_date)):
                    writer.writerow({
                        'UserName': req.user_name,
                        'PreferenceRank': req.preference_rank,
                        'Hut': req.hut_name,
                        'StartDate': req.start_date.strftime('%Y-%m-%d'),
                        'EndDate': req.end_date.strftime('%Y-%m-%d'),
                        'PartySize': req.party_size,
                        'TraverseGroup': req.traverse_group or '',
                        'Sanctioned': 'YES' if req.is_sanctioned else '',
                        'Status': 'UNASSIGNED'
                    })

def save_alternatives_to_csv(suggestions, filename):
    """
    Save alternative suggestions for unassigned users.

    Output format:
    UserName,AlternativeHut,Dates,PartySize,Note
    """
    with open(filename, 'w', newline='') as f:
        fieldnames = ['UserName', 'AlternativeHut', 'Dates', 'PartySize', 'Note']
        writer = csv.DictWriter(f, fieldnames=fieldnames)

        writer.writeheader()

        for user, alternatives in sorted(suggestions.items()):
            if alternatives:
                for alt in alternatives:
                    writer.writerow({
                        'UserName': user,
                        'AlternativeHut': alt['hut'],
                        'Dates': alt['dates'],
                        'PartySize': alt['party_size'],
                        'Note': alt['note']
                    })
            else:
                writer.writerow({
                    'UserName': user,
                    'AlternativeHut': 'N/A',
                    'Dates': 'N/A',
                    'PartySize': 'N/A',
                    'Note': 'No alternatives available'
                })

def generate_sample_csv(filename, num_users=10):
    """Generate sample CSV data for testing."""
    import random

    huts = ['Bradley', 'Benson', 'Peter Grubb', 'Ludlow']
    first_names = ['Alice', 'Bob', 'Carol', 'David', 'Emma', 'Frank', 'Grace', 'Henry', 'Iris', 'Jack',
                   'Kate', 'Leo', 'Maya', 'Noah', 'Olivia', 'Paul', 'Quinn', 'Ruby', 'Sam', 'Tina']
    last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis', 'Rodriguez', 'Martinez']

    with open(filename, 'w', newline='') as f:
        fieldnames = ['UserName', 'PreferenceRank', 'Hut', 'StartDate', 'EndDate', 'PartySize']
        writer = csv.DictWriter(f, fieldnames=fieldnames)

        writer.writeheader()

        for i in range(num_users):
            user_name = f"{random.choice(first_names)} {random.choice(last_names)}"
            base_party_size = random.randint(2, 8)

            # Generate 5 preferences
            for pref_rank in range(1, 6):
                hut = random.choice(huts)

                # Random date in season (Dec 2025 - May 2026)
                # Bias towards winter months (Dec-Feb)
                if random.random() < 0.6:
                    # Winter months
                    month = random.randint(12, 12) if random.random() < 0.33 else random.randint(1, 2)
                    year = 2025 if month == 12 else 2026
                else:
                    # Spring months
                    month = random.randint(3, 5)
                    year = 2026

                day = random.randint(1, 28)  # Safe day range
                start_date = datetime(year, month, day)

                # Random stay length 1-4 nights
                num_nights = random.randint(1, 4)
                end_date = datetime(year, month, min(day + num_nights, 28))

                # Slight variation in party size across preferences
                party_size = base_party_size + random.randint(-1, 1)
                party_size = max(1, min(party_size, 15))  # Clamp to reasonable range

                writer.writerow({
                    'UserName': user_name,
                    'PreferenceRank': pref_rank,
                    'Hut': hut,
                    'StartDate': start_date.strftime('%Y-%m-%d'),
                    'EndDate': end_date.strftime('%Y-%m-%d'),
                    'PartySize': party_size
                })

    print(f"Generated sample data: {filename}")
