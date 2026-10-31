from urllib.parse import urlencode

import markdown as markdown_lib
import nh3
from django import template
from django.conf import settings
from django.urls import reverse, translate_url
from django.utils.html import format_html_join
from django.utils.safestring import mark_safe

from apps.core import navigation

register = template.Library()

# Balises autorisées dans le Markdown des pages éditoriales : tout le reste est retiré.
MARKDOWN_TAGS = {
    "a", "blockquote", "br", "code", "em", "h2", "h3", "h4", "hr", "li", "ol", "p", "pre",
    "strong", "table", "tbody", "td", "th", "thead", "tr", "ul",
}  # fmt: skip


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


@register.simple_tag(takes_context=True)
def public_navigation(context):
    return navigation.build(context["request"].path)


@register.filter
def render_markdown(text):
    html = markdown_lib.markdown(text or "", extensions=["tables", "sane_lists"])
    return mark_safe(nh3.clean(html, tags=MARKDOWN_TAGS, link_rel="noopener"))
