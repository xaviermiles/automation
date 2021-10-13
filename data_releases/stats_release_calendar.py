"""
Use Release calendar to trigger updates to Stats API services (proof-of-concept)

> Should be run before 10:45am as the events get deleted soon after
> .ics file could be parsed manually fairly easily if "ics" package couldn't be
installed
"""

import os, glob
import pytz
from datetime import datetime, time

import requests
from ics import Calendar, Event

TZONE = pytz.timezone('Pacific/Auckland')
API_SERVICE_EVENTS = ["Example1", "Example2"]

r = requests.get("https://www.stats.govt.nz/release-calendar/calendar-export")
releases_ics = r.content.decode()

# Save a copy (and clear old copies)
current_dt = datetime.now(tz=TZONE).replace(second=0, microsecond=0).isoformat()
fname_format = '../data/stats_releases_*.ics'
for f in glob.glob(fname_format):
    os.remove(f)
with open(fname_format.replace('*', current_dt), 'w') as f:
    f.write(releases_ics)

# Do any events correspond to an API services that should be updated today?
releases = Calendar(releases_ics)
for e in releases.events:
    if (e.begin.date() == datetime.now(tz=TZONE).date() and
        e.name in API_SERVICE_EVENTS):
        # trigger Pentaho workflow? or add to list that triggers multiple WFs
        pass
        if e.begin.time() != time(hour=10, minute=45):
            # events should be at 10:45am -> maybe trigger email warning?
            pass
