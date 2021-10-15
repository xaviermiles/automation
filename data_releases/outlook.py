import re
from datetime import datetime, timedelta
from bs4 import BeautifulSoup as bs

from O365 import Account, FileSystemTokenBackend

import utils

DEFAULT_TZONE = pytz.timezone('Pacific/Auckland')


def get_account(scopes):
    config = utils.read_config()
        
    credentials = (config['o365']['client_id'], config['o365']['client_secret'])
    # replace FileSystemTokenBackend with FirestoreBackend ??
    token_backend = FileSystemTokenBackend(token_filename='o365_token.txt')
    account = Account(credentials, token_backend=token_backend)
    
    if not account.is_authenticated:
        account.authenticate(scopes=scopes)
    # else:
    #     # is this doing anything?
    #     con = Connection(credentials, scopes=scopes)
    #     con.refresh_token()
    return account


def get_covid_calendar():
    account = get_account(['basic', 'calendar_shared_all'])
    schedule = account.schedule()
    calendar = schedule.get_calendar(calendar_name='COVID Release Calendar')
    return calendar


def get_next_info(calendar, days, tzone=DEFAULT_TZONE):
    """
    
    tzone - this must be an instance of a tzinfo subclass
    Return (some) information about the calendar events in the next {days} days,
    ordered by expected release-datetime.
    """
    if not isinstance(days, int) or days < 1:
        raise ValueError("{days} should be positive integer")
    
    current_date = datetime.now(tzone).date()
    q = calendar.new_query('start').greater(current_date - timedelta(days=1))
    q.chain('and').on_attribute('end') \
                  .less(current_date + timedelta(days=days + 1))
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
            'release_dt': r.start.astimezone(tzone).isoformat(),
            'files': [file.group(1).strip() for file in files_re],
            'url': url if url_re else None,
            'script': scripts if scripts_re else None
        })
        
    next_info_sorted = sorted(next_info, key=lambda k: k['release_dt'])
    return next_info_sorted


def move_event(calendar, ical_uid, days=0, hours=0, minutes=0):
    """
    Move event by number of days+hours+minutes - positive values will move event
    forwards, negative backwards.
    """
    tchange = timedelta(days=days, hours=hours, minutes=minutes)
    q = calendar.new_query('ical_uid').equals(ical_uid)
    event = list(calendar.get_events(query=q))[0]
    event.start = event.start + tchange
    event.end = event.end + tchange
    event.save()
    
    
def cancel_event(calendar, ical_uid, tzone=DEFAULT_TZONE):
    """
    Cancels event in Outlook calendar on current date (if it exists)

    tzone - this must be an instance of a tzinfo subclass

    Recurring events share the same `ical_uid` across each date, so removing
    these events requires specifying lower/upper dates to delete between. This
    function will only delete a single occurence, not the series of events.
    (NB: Recurring events is why this only deletes events on the current date.)
    """
    current_date = datetime.now(tzone).date()
    q = calendar.new_query('ical_uid').equals(ical_uid)
    q.chain('and').on_attribute('start') \
                  .greater(current_date - timedelta(days=1))
    q.chain('and').on_attribute('end') \
                  .less(current_date + timedelta(days=1))

    events = list(calendar.get_events(query=q))
    if len(events) > 1:
        err_msg = ("This function is for deleting a single event at a time. "
                   "There is multiple events with the same `ical_uid` today.")
        raise NotImplementedError(err_msg)
    elif len(events) == 1:
        e = events[0]
        e.cancel_event()
        e.save()
    # else: no event to delete


def email_alert(message, subject=""):
    config = utils.read_config()
    account = get_account(['basic', 'message_all'])
    mailbox = account.mailbox()
    
    m = mailbox.new_message()
    m.to.add(config['alert_email_addresses'])
    m.subject = "Alert!! from automation"
    if subject:
        m.subject += f"- {subject}"
    m.body = message
    m.send()
