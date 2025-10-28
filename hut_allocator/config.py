from datetime import datetime

# Hut Configuration
HUTS = {
    "Bradley": 15,
    "Benson": 12,
    "Peter Grubb": 15,
    "Ludlow": 15
}

# Season Configuration
SEASON_START = datetime(2025, 12, 1)
SEASON_END = datetime(2026, 5, 31)

# Scoring weights for preferences
PREFERENCE_SCORES = {
    1: 100,  # First choice
    2: 50,   # Second choice
    3: 25,   # Third choice
    4: 10,   # Fourth choice
    5: 5     # Fifth choice
}

# Optimization parameters
NUM_ITERATIONS = 20
TIMEOUT_SECONDS = 300
NUM_SWAP_ATTEMPTS = 50
