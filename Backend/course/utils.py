import datetime
import os
import random
import string
import re
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _


def random_string_generator(size=10, chars=string.ascii_lowercase + string.digits):
    return "".join(random.choice(chars) for _ in range(size))


def unique_slug_generator(instance, new_slug=None):
    """
    This is for a Django project and it assumes your instance
    has a model with a slug field and a title character (char) field.
    """
    if new_slug is not None:
        slug = new_slug
    else:
        slug = slugify(instance.title)

    Klass = instance.__class__
    qs_exists = Klass.objects.filter(slug=slug).exists()
    if qs_exists:
        new_slug = "{slug}-{randstr}".format(
            slug=slug, randstr=random_string_generator(size=4)
        )
        return unique_slug_generator(instance, new_slug=new_slug)
    return slug


def extract_youtube_id(url):
    """
    Extrae el ID de video de una URL de YouTube.
    Soporta varios formatos de URL de YouTube.
    """
    youtube_regex = (
        r'(?:https?:\/\/)?'
        r'(?:www\.)?'
        r'(?:youtube\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|\S*?[?&]v=)|youtu\.be\/)([a-zA-Z0-9_-]{11})'
    )
    
    match = re.search(youtube_regex, url)
    return match.group(1) if match else None


def get_video_embed_url(url):
    """
    Convierte una URL de video en una URL embebible.
    Actualmente soporta YouTube y URLs directas de video.
    """
    if not url:
        return None
        
    # Procesar URLs de YouTube
    youtube_id = extract_youtube_id(url)
    if youtube_id:
        return f"https://www.youtube.com/embed/{youtube_id}"
    
    # Si es una URL de Vimeo
    vimeo_regex = r'(?:https?:\/\/)?(?:www\.)?(?:vimeo\.com\/)([0-9]+)'
    vimeo_match = re.search(vimeo_regex, url)
    if vimeo_match:
        return f"https://player.vimeo.com/video/{vimeo_match.group(1)}"
    
    # Para otros casos, devolver la URL original
    return url


def get_generic_embed_url(url: str) -> str:
    """Transform common presentation URLs (Prezi, Canva, Google Slides) into embeddable URLs.

    This is best-effort. If pattern is unknown, returns the original URL.
    """
    if not url:
        return url

    # Prezi
    if "prezi.com" in url:
        # Match /view/{id}/ or /p/{id}/ ...
        m = re.search(r"prezi\.com\/(?:view|p)\/([a-zA-Z0-9_-]+)", url)
        if m:
            prezi_id = m.group(1)
            return f"https://prezi.com/view/{prezi_id}/"
        # Fallback: try last path segment
        parts = url.rstrip('/').split('/')
        if parts:
            return f"https://prezi.com/view/{parts[-1]}/"

    # Canva
    if "canva.com" in url:
        # Match /design/{id}
        m = re.search(r"canva\.com\/design\/([a-zA-Z0-9_-]+)", url)
        if m:
            canva_id = m.group(1)
            return f"https://www.canva.com/design/{canva_id}/view?embed"

        # Older watch links
        m = re.search(r"canva\.com\/design\/([a-zA-Z0-9_-]+)\/watch", url)
        if m:
            canva_id = m.group(1)
            return f"https://www.canva.com/design/{canva_id}/view?embed"

    # Google Slides
    if "docs.google.com/presentation" in url:
        m = re.search(r"presentation\/d\/([a-zA-Z0-9_-]+)", url)
        if m:
            slides_id = m.group(1)
            return f"https://docs.google.com/presentation/d/{slides_id}/embed?start=false&loop=false&delayms=3000"

    return url
