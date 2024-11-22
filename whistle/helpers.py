import re
from django.utils.translation import gettext

from whistle.settings import notification_manager


def notify(recipient, event, actor=None, object=None, target=None, details=''):
    notification_manager.notify(recipient=recipient, event=event, actor=actor, object=object, target=target,
                                details=details)


def strip_unwanted_chars(str):
    pat = re.compile(r'%\(.*\)s|"%\(.*\)s"|%\(.*\)r|"%\(.*\)r"')
    str = re.sub(pat, '', gettext(str))  # remove all variable placeholders
    str = str.replace("''", '')  # remove all 2 single quotas
    str = str.replace('""', '')  # remove all 2 double quotas
    str = str.replace('()', '')  # remove empty braces
    str = str.strip(' :.')  # remove trailing spaces and semicolons
    str = re.sub(' +', ' ', str)  # remove all multiple spaces
    return str
