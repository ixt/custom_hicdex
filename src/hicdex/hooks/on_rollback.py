import os
import datetime

import requests

from dipdup.context import HookContext
from dipdup.datasources.datasource import Datasource
from dipdup.enums import ReindexingReason

from datetime import datetime


def send(levels_diff):
    api_key = os.environ.get('MAILGUN_API_KEY')
    if not api_key:
        return
    to_emails = os.environ.get('NOTIFIED_EMAILS').split(',')
    mail_from = os.environ.get('MAIL_FROM')

    return requests.post(
        "https://api.eu.mailgun.net/v3/mail.hicdex.com/messages",
        auth=("api", api_key),
        data={
            "from": f"Hicdex API <{mail_from}>",
            "to": to_emails,
            "subject": os.environ.get('MAIL_SUBJECT'),
            "text": f"Chain reorg: {levels_diff} blocks, please reindex!",
        },
    )


async def on_rollback(
    ctx: HookContext,
    datasource: Datasource,
    from_level: int,
    to_level: int,
) -> None:
    ctx.logger.warning(
        'Datasource rolled back from level %s to level %s, reindexing', from_level, to_level)
    levels_diff = from_level - to_level
    sttime = datetime.now().strftime('%Y%m%d-%H%M%S')
    with open('/home/biker/hicdex/infos/reorg.txt', 'a') as logfile:
        logfile.write(f'{sttime} # {from_level} -> {to_level}\n')
    send(levels_diff)
