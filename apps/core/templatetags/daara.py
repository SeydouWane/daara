from urllib.parse import urlencode

from django import template
from django.conf import settings
from django.urls import reverse, translate_url
from django.utils.html import format_html_join

register = template.Library()


@register.simple_tag(takes_context=True)
def hreflang_links(context):
    """Balises hreflang réciproques, plus x-default vers la langue par défaut (spec §5.3)."""
    request = context["request"]
    url = request.build_absolute_uri(request.path)
    links = [(code, translate_url(url, code)) for code, _name in settings.LANGUAGES]
    links.append(("x-default", translate_url(url, settings.LANGUAGE_CODE)))
    return format_html_join("\n", '<link rel="alternate" hreflang="{}" href="{}">', links)


@register.simple_tag(takes_context=True)
def switch_language_url(context, lang):
    request = context["request"]
    query = urlencode({"next": request.get_full_path()})
    return f"{reverse('switch_language', args=[lang])}?{query}"
