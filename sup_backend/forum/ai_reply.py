"""
AI reply engine for the salaryfree forum.

PRIVACY CONTRACT
----------------
Claude is NEVER given any user-specific financial data.
The prompt contains only the thread title and body as written by the user.
The system prompt explicitly prohibits referencing personal financial details.
This is enforced here — not just by policy — by never passing financial
model data to this module.
"""

import logging
import os
import threading
import time

logger = logging.getLogger(__name__)

# Delay before posting AI reply (seconds). Feels organic, not instant-bot.
AI_REPLY_DELAY = 90  # 1.5 minutes

# Bedrock cross-region inference profile for Claude Haiku
BEDROCK_MODEL_ID = os.environ.get('ANTHROPIC_DEFAULT_HAIKU_MODEL', 'us.anthropic.claude-haiku-4-5-20251001-v1:0')

SYSTEM_PROMPT = """\
You are Asha, a warm and knowledgeable advisor on salaryfree — a platform that helps \
salaried Indians think through financial independence, founder leaps, early retirement, \
and related life decisions.

Your role is to engage thoughtfully with community posts — adding context, asking a \
clarifying question, sharing a relevant perspective, or pointing to a useful framework.

HARD RULES — never break these:
1. Do NOT reference, reveal, infer, or estimate any specific financial figures about the \
person who wrote the post — no income, savings, expenses, assets, or investment amounts, \
even if they seem implied by the post.
2. Do NOT give personalised financial advice or tell anyone what they should do with \
their money.
3. Keep responses concise — 2 to 4 short paragraphs maximum.
4. Write in plain, conversational English. No bullet lists, no headers.
5. Respond only to the topic of the post, not to user identity.

If the post is about Indian financial independence contexts (FIRE, founder salary, \
R2I, sabbaticals, layoffs), draw on your knowledge of Indian tax, inflation, market \
norms, and the typical emotional arc of these decisions.
"""


def schedule_ai_reply(thread_id: int) -> None:
    """
    Kick off a background thread that will post an AI reply after a delay.
    Safe to call from a Django view — does not block the request.
    """
    t = threading.Thread(
        target=_delayed_reply,
        args=(thread_id,),
        daemon=True,
        name=f'ai-reply-{thread_id}',
    )
    t.start()


def _delayed_reply(thread_id: int) -> None:
    time.sleep(AI_REPLY_DELAY)
    try:
        _generate_and_save(thread_id)
    except Exception:
        logger.exception('AI reply failed for thread %s', thread_id)
    finally:
        # Each thread needs to close its own DB connection to avoid leaks
        from django.db import connection
        connection.close()


def _generate_and_save(thread_id: int) -> None:
    # Import inside function to avoid app-registry issues at module load time
    from forum.models import Reply, Thread

    try:
        thread = Thread.objects.get(pk=thread_id, is_visible=True)
    except Thread.DoesNotExist:
        return

    if thread.ai_replied:
        return

    try:
        import anthropic
    except ImportError:
        logger.error('anthropic package not installed — run: pip install anthropic')
        return

    # AnthropicBedrock uses the boto3 credential chain (AWS_PROFILE / ~/.aws/credentials)
    client = anthropic.AnthropicBedrock()

    user_message = f"Post title: {thread.title}\n\n{thread.body}"

    message = client.messages.create(
        model=BEDROCK_MODEL_ID,
        max_tokens=512,
        system=SYSTEM_PROMPT,
        messages=[{'role': 'user', 'content': user_message}],
        metadata={'user_id': 'salaryfree'},
    )

    reply_text = message.content[0].text.strip()

    Reply.objects.create(
        thread=thread,
        author=None,
        body=reply_text,
        is_ai=True,
    )

    thread.ai_replied = True
    thread.save(update_fields=['ai_replied'])
    logger.info('AI reply posted for thread %s', thread_id)
