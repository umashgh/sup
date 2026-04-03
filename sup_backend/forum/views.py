from django.core.paginator import Paginator
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .ai_reply import schedule_ai_reply
from .models import Reaction, Reply, Thread

REACTIONS = [
    ('helpful',   'Helpful',   '💡'),
    ('relatable', 'Relatable', '❤️'),
    ('inspiring', 'Inspiring', '🔥'),
]

LOGIN_URL = '/accounts/login/'


def _requires_login(request):
    """Redirect to login with next= pointing back here."""
    return redirect(f'{LOGIN_URL}?next={request.path}')


def forum_list(request):
    threads = Thread.objects.filter(is_visible=True).prefetch_related('reactions', 'replies')
    paginator = Paginator(threads, 20)
    page = paginator.get_page(request.GET.get('page', 1))
    return render(request, 'forum/list.html', {'page': page, 'reactions': REACTIONS})


def thread_detail(request, pk):
    thread = get_object_or_404(Thread, pk=pk, is_visible=True)
    replies = thread.replies.select_related('author')

    user_reactions = set()
    if request.user.is_authenticated:
        user_reactions = set(
            Reaction.objects.filter(thread=thread, user=request.user)
            .values_list('reaction_type', flat=True)
        )

    reaction_counts = {
        rtype: thread.reactions.filter(reaction_type=rtype).count()
        for rtype, _, _ in REACTIONS
    }

    return render(request, 'forum/thread.html', {
        'thread': thread,
        'replies': replies,
        'reactions': REACTIONS,
        'reaction_counts': reaction_counts,
        'user_reactions': user_reactions,
        'can_interact': request.user.is_authenticated,
    })


_SCENARIO_DEFAULTS = {
    'FOUNDER': {
        'title': 'Thinking about the leap — is my timing right?',
        'body': (
            "I've been running the numbers on leaving my job to go full-time on my venture "
            "and I keep going back and forth. Part of me feels ready, part of me wonders if "
            "I'm missing something obvious.\n\n"
            "Has anyone been through this? What made you feel like the time was actually right?"
        ),
    },
    'RETIREMENT': {
        'title': 'Planning my retirement — what am I not thinking about?',
        'body': (
            "I've been working through my retirement plan and feel reasonably prepared on "
            "the numbers side, but I wonder what I might be missing — the non-financial "
            "stuff especially.\n\n"
            "What surprised you most about the transition? What do you wish you'd planned for?"
        ),
    },
    'R2I': {
        'title': 'Seriously considering moving back to India — anyone been through this?',
        'body': (
            "I've been thinking about R2I for a while and I'm starting to take it seriously. "
            "The financial side is one piece of it but honestly the lifestyle adjustments "
            "feel more uncertain.\n\n"
            "What were the things you didn't anticipate? What made it easier or harder?"
        ),
    },
    'HALF_FIRE': {
        'title': 'Exploring part-time work while staying financially independent',
        'body': (
            "I'm at a point where I could step back from full-time work without fully retiring "
            "— maybe consulting, maybe something passion-driven. But I keep second-guessing "
            "whether I'm being realistic.\n\n"
            "Has anyone made this work? How did you structure it?"
        ),
    },
    'TERMINATION': {
        'title': 'Navigating a job change — figuring out what comes next',
        'body': (
            "I'm in the middle of a job transition and trying to figure out how to make the "
            "most of this window. There's a mix of anxiety and possibility, honestly.\n\n"
            "For those who've been through this — what helped you think clearly about next steps?"
        ),
    },
}


def create_thread(request):
    if not request.user.is_authenticated:
        return _requires_login(request)

    # Look up user's active scenario for smart defaults
    scenario_defaults = {}
    try:
        from core.models import ScenarioProfile
        sp = ScenarioProfile.objects.get(user=request.user)
        scenario_defaults = _SCENARIO_DEFAULTS.get(sp.scenario_type, {})
    except Exception:
        pass

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        body = request.POST.get('body', '').strip()
        errors = {}

        if not title:
            errors['title'] = 'Please add a title.'
        elif len(title) > 200:
            errors['title'] = 'Title must be under 200 characters.'
        if not body:
            errors['body'] = 'Please share your thought.'

        if not errors:
            thread = Thread.objects.create(
                author=request.user,
                title=title,
                body=body,
            )
            schedule_ai_reply(thread.pk)
            return redirect('forum:thread', pk=thread.pk)

        return render(request, 'forum/create.html', {
            'errors': errors,
            'title': title,
            'body': body,
        })

    return render(request, 'forum/create.html', {
        'default_title': scenario_defaults.get('title', ''),
        'default_body': scenario_defaults.get('body', ''),
    })


@require_POST
def react(request, pk):
    if not request.user.is_authenticated:
        return HttpResponse(status=403)

    thread = get_object_or_404(Thread, pk=pk, is_visible=True)
    reaction_type = request.POST.get('reaction_type')

    valid_types = {r[0] for r in REACTIONS}
    if reaction_type not in valid_types:
        return HttpResponse(status=400)

    obj, created = Reaction.objects.get_or_create(
        thread=thread, user=request.user, reaction_type=reaction_type
    )
    if not created:
        obj.delete()

    thread.update_score()

    reaction_counts = {
        rtype: thread.reactions.filter(reaction_type=rtype).count()
        for rtype, _, _ in REACTIONS
    }
    user_reactions = set(
        Reaction.objects.filter(thread=thread, user=request.user)
        .values_list('reaction_type', flat=True)
    )

    return render(request, 'forum/_reactions.html', {
        'thread': thread,
        'reactions': REACTIONS,
        'reaction_counts': reaction_counts,
        'user_reactions': user_reactions,
    })


@require_POST
def add_reply(request, pk):
    if not request.user.is_authenticated:
        return redirect(f'{LOGIN_URL}?next=/forum/{pk}/')

    thread = get_object_or_404(Thread, pk=pk, is_visible=True)
    body = request.POST.get('body', '').strip()

    if body and len(body) >= 5:
        Reply.objects.create(thread=thread, author=request.user, body=body, is_ai=False)
        thread.update_score()

    return redirect('forum:thread', pk=pk)
