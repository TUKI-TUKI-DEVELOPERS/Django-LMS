from django import template
import re
from urllib.parse import urlparse, parse_qs

register = template.Library()


def _extract_youtube_id(url: str) -> str:
    try:
        parsed = urlparse(url)
        host = parsed.netloc.lower()
        path = parsed.path
        if 'youtu.be' in host:
            # https://youtu.be/<id>
            vid = path.strip('/').split('/')[0]
            return vid
        if 'youtube.com' in host:
            if path.startswith('/watch'):
                qs = parse_qs(parsed.query)
                if 'v' in qs and qs['v']:
                    return qs['v'][0]
            # /embed/<id> or /shorts/<id>
            m = re.search(r"/(?:embed|shorts)/([A-Za-z0-9_-]{6,})", path)
            if m:
                return m.group(1)
        return ''
    except Exception:
        return ''


def _extract_vimeo_id(url: str) -> str:
    try:
        m = re.search(r"vimeo\.com/(?:video/)?(\d+)", url)
        return m.group(1) if m else ''
    except Exception:
        return ''


@register.filter(name="to_embed_url")
def to_embed_url(url: str) -> str:
    """Convert a public media URL to an embeddable URL (YouTube/Vimeo). Fallback: original URL."""
    if not url:
        return ''
    # Normalize weird placeholder values
    text = str(url).strip()
    if not text or text in ('[]', '{}', 'null', 'None', 'undefined'):
        return ''

    yt_id = _extract_youtube_id(text)
    if yt_id:
        return f"https://www.youtube.com/embed/{yt_id}?rel=0"

    vm_id = _extract_vimeo_id(text)
    if vm_id:
        return f"https://player.vimeo.com/video/{vm_id}"

    return text


@register.filter(name="completed_for")
def completed_for(progress_iterable, lesson) -> bool:
    """Return True if the given lesson is marked completed in the iterable of StudentProgress."""
    try:
        lesson_id = getattr(lesson, 'id', None)
        for p in progress_iterable or []:
            if getattr(p, 'lesson_id', None) == lesson_id and getattr(p, 'is_completed', False):
                return True
    except Exception:
        return False
    return False


