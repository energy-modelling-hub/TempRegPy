import pandas as pd
from .constants import *
from ..logging_config import *

def process_dates_to_groups(dates):
    date_groups = []

    global_counter = 0

    sunday_counter = 0

    for date in dates:
        
        if date.weekday() < 5:  # Monday to Friday
            if date in [pd.Timestamp('2023-01-01'), pd.Timestamp('2023-01-02')]:  # Specific dates
                date_groups.append(sunday_counter)
            else:
                date_groups.append(global_counter)
        elif date.weekday() == 5:  # Saturday
            global_counter += 1
            date_groups.append(global_counter)
        else:  # Sunday
            global_counter += 1
            date_groups.append(global_counter)
            sunday_counter = global_counter
            global_counter += 1

    return date_groups
