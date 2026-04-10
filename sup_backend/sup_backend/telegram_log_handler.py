"""
Custom logging handler that sends Django ERROR logs to Telegram.
Handles 500 errors (django.request) and security alerts (django.security).
Uses only stdlib — no Django ORM, safe to use during startup.
"""
import logging
import urllib.parse
import urllib.request


class TelegramHandler(logging.Handler):

    def __init__(self, token='', chat_id='', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.token   = token
        self.chat_id = str(chat_id)

    def emit(self, record):
        if not self.token or not self.chat_id:
            return
        try:
            msg  = self.format(record)
            text = f"🔴 *salaryfree.in* — {record.levelname}\n\n`{msg[:3500]}`"
            url  = f"https://api.telegram.org/bot{self.token}/sendMessage"
            data = urllib.parse.urlencode({
                'chat_id':    self.chat_id,
                'text':       text,
                'parse_mode': 'Markdown',
            }).encode()
            urllib.request.urlopen(
                urllib.request.Request(url, data=data),
                timeout=5,
            )
        except Exception:
            pass  # never let alerting break the app
