import re
import json
import pytz
from datetime import date, datetime, timedelta
from bs4 import BeautifulSoup as bs

import yaml
from O365 import Account, Connection, FileSystemTokenBackend
from O365.calendar import Event


def get_covid_calendar():
    with open('../config.yaml', 'r') as f:
        config = yaml.load(f, Loader=yaml.BaseLoader)
        
    credentials = (config['o365']['client_id'], config['o365']['client_secret'])
    # replace FileSystemTokenBackend with FirestoreBackend ??
    token_backend = FileSystemTokenBackend(token_filename='o365_token.txt')
    account = Account(credentials, token_backend=token_backend)
    
    scopes = ['basic', 'calendar_shared_all']
    if not account.is_authenticated:
        account.authenticate(scopes=scopes)
    # else:
    #     # is this doing anything?
    #     con = Connection(credentials, scopes=scopes)
    #     con.refresh_token()
    
    schedule = account.schedule()
    covid_calendar = schedule.get_calendar(calendar_name='COVID Release Calendar')
    
    return covid_calendar


def get_next_info(calendar, days):
    """
    Return (some) information about the calendar events in the next {days} days,
    ordered by expected release-datetime.
    """
    TIMEZONE = pytz.timezone('Pacific/Auckland')
    
    q = calendar.new_query('start').greater(date.today() - timedelta(days=1))
    q.chain('and').on_attribute('end') \
                  .less(date.today() + timedelta(days=days + 1))
    next_responses = calendar.get_events(query=q, include_recurring=True)
    
    next_info = []
    for r in next_responses:
        files_re = re.finditer(r'files:(.*)\n', r.body, flags=re.I)
        url_re = re.search(r'url:(.*)\n', r.body, flags=re.I)
        if url_re:
            url = bs(url_re.group(1), 'html.parser').find('a').get('href')
        scripts_re = re.search(r'script:(.*)', r.body, flags=re.I)
        if scripts_re:
            scripts = bs(scripts_re.group(1), 'html.parser').get_text().strip()
        next_info.append({
            'ical_uid': r.ical_uid,
            'title': r.subject,
            'release_dt': r.start.astimezone(TIMEZONE).isoformat(),
            'files': [file.group(1).strip() for file in files_re],
            'url': url if url_re else None,
            'script': scripts if scripts_re else None
        })
        
    next_info_sorted = sorted(next_info, key=lambda k: k['release_dt'])
    return next_info_sorted


def move_event(ical_uid, days, hours, minutes):
    """
    Move event by number of days+hours+minutes - positive values will move event
    forwards, negative backwards.
    """
    tchange = timedelta(days=days, hours=hours, minutes=minutes)
    q = covid_calendar.new_query('ical_uid').equals(ical_uid)
    event = list(covid_calendar.get_events(query=q))[0]
    event.start = event.start + tchange
    event.end = event.end + tchange
    event.save()
    

if __name__ == "__main__":
    covid_calendar = get_covid_calendar()
    next_week = get_next_info(covid_calendar, 1)
    
    
    output = {
        'next_dt': next_week[0]['release_dt'],
        'calendar_id': covid_calendar.calendar_id,
        'meta': "Gives datetimes according to New Zealand timezone.",
        'full_info': next_week
    }
    with open('../data/next_week.json', 'w') as f:
        json.dump(output, f)

