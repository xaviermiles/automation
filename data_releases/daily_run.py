"""
Coordinates checking data releases for sites due, according to Outlook calendar.

Run this script at the beginning of the day and it will end itself after
checking the last event in Outlook calendar.
"""
import time
import json
from datetime import datetime, timedelta

import schedule

from data_releases import outlook, site_checking
    
    
def coordinate(event_details, tzone):
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
        # detected a data release
        msg = """
        Data released for "{title}" with date "{date_str}"
        
        Download from: {url}
        
        :^)
        """.format(**event_details)
        outlook.email_alert(msg, subject="Data Release Detected")
        # remove calendar entry -- DISABLED FOR TESTING
        # outlook.cancel_event(covid_calendar, event_details['ical_uid'])
        # cancel retry-jobs
        schedule.clear(event_details['ical_uid'])
    elif len(schedule.get_jobs(event_details['ical_uid'])) == 0:
        # no more retries scheduled, move calendar event to next weekday
        if datetime.now(tzone).strftime('%A') == "Friday":
            days_to_add = 3
        else:
            days_to_add = 1
        outlook.move_event(covid_calendar, event_details['ical_uid'],
                           days = days_to_add)
    elif updated is None:
        # error was thrown when checking site
        msg = """
        Error was thrown when checking data release for {event_name}.
        (This event will not be automatically retried.)
        
        Error message: {response_info}
        
        Full event details:
        {event_details}
        """.format(event_details=event_details,
                   response_info=response_info,
                   event_name=event_details['title'])
        outlook.email_alert(msg, subject="Data Release Error")
        # abandon retries for this event
        schedule.clear(event_details['ical_uid'])


def check_for_elapsed_events(next_day_info, tzone):
    # The events are sorted by datetime, so the first element is the next event
    next_event = next_day_info[0]
    next_dt = datetime.fromisoformat(next_event['release_dt'])
    if next_dt < datetime.now(tzone):
        # Event has elapsed so should be put on "active" status
        schedule.every(5).minutes.do(coordinate,
                                     event_details=next_event,
                                     tzone=tzone) \
                .until(datetime.now(tzone) + timedelta(minutes=30)) \
                .tag(next_event['ical_uid'])
        # ...and removed from "pending"
        if len(next_day_info) > 1:
            next_day_info = next_day_info[1:]
        else:
            # no more events to check for
            schedule.clear('main_job')
    
    return next_day


if __name__ == "__main__":
    covid_calendar = outlook.get_covid_calendar()
    
    next_day = outlook.get_next_info(covid_calendar, 1)
    output = {
        'next_dt': next_day[0]['release_dt'] if len(next_day) > 0 else None,
        'calendar_id': covid_calendar.calendar_id,
        'meta': """
        Gives datetimes according to "{tzone}" timezone ({tzname}).
        """.format(tzone=outlook.DEFAULT_TZONE,
                   tzname=outlook.DEFAULT_TZONE.tzname(datetime.now())),
        'full_info': next_day
    }
    with open('../data/next_day.json', 'w') as f:
        json.dump(output, f)
    
    # Start running
    schedule.every(15).minutes.do(check_for_elapsed_events,
                                  next_day_info=next_day,
                                  tzone=outlook.DEFAULT_TZONE) \
            .tag('main_job')
    
    while len(schedule.get_jobs()) > 0:
        schedule.run_pending()
        time.sleep(1)
