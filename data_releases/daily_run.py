"""
Coordinates checking data releases for sites due, according to Outlook calendar.

Run this script at the beginning of the day and it will end itself after
checking the last event in Outlook calendar.
"""
import time
import json
from datetime import datetime

import tzlocal
import schedule

from data_releases import outlook, site_checking
    
    
def coordinate(event_details):
    """
    If check is successful (or throws error) alert via Outlook Email and remove
    Outlook Calendar entry
    """
    # Should {url,text_template,xpath} be stored somewhere other than the event?
    updated, response_info = site_checking.check_date_str(
        event_details['url'],
        event_details['text_template'],
        event_details['date_str'],
        xpath=event_details['xpath']
    )
    if updated:
        # email alert
        msg = """
        Data released for "{title}" with date "{date_str}"
        
        Download from: {url}
        
        :^)
        """.format(**event_details)
        outlook.email_alert(msg, subject="Data Release Detected")
        # remove calendar entry
        outlook.cancel_event(covid_calendar, event_details['ical_uid'])
        # cancel retry-jobs
        schedule.clear(event_details['ical_uid'])



def check_for_elapsed_events():
    # The events sorted by datetime, so the first element is the next event
    next_event = next_day[0]
    next_dt = datetime.fromisoformat(next_event['release_dt'])
    if next_dt < datetime.now(system_tzone):
        # Event has elapsed so should be put on "active" status
        schedule.every(5).minutes.until.do(coordinate, info=next_event) \
                .tags(next_event['ical_uid'])
        # ...and removed from "pending"
        if len(next_day) > 1:
            next_day = next_day[1:]
        else:
            schedule.clear('main_job')  # no more events to check for
            

if __name__ == "__main__":
    # Setup
    system_tzone = tzlocal.get_localzone()
    print(system_tzone)
    
    covid_calendar = outlook.get_covid_calendar()
    next_day = outlook.get_next_info(covid_calendar, 1, system_tzone)
    
    output = {
        'next_dt': next_day[0]['release_dt'] if len(next_day) > 0 else None,
        'calendar_id': covid_calendar.calendar_id,
        'meta': "Gives datetimes according to the system's timezone.",
        'full_info': next_day
    }
    with open('../data/next_day.json', 'w') as f:
        json.dump(output, f)
    
    # Start running
    schedule.every(15).minutes.do(check_for_elapsed_events) \
            .tag('main_job')
    
    # while len(schedule.get_jobs()) > 0:
    #     schedule.run_pending()
    #     time.sleep(1)
