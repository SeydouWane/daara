from urllib.parse import urlencode

import markdown as markdown_lib
import nh3
from django import template
from django.conf import settings
from django.urls import reverse, translate_url
from django.utils.html import format_html, format_html_join
from django.utils.safestring import mark_safe
from django.utils.text import capfirst
from django.utils.translation import gettext as _

from apps.core import navigation
from apps.core.images import rendition_name, rendition_widths
from apps.members.permissions import is_back_office, may

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


@register.simple_tag
def responsive_image(field_file, widths, sizes, alt="", css_class="", eager=False):
    """<img> en WebP aux largeurs disponibles, dimensions explicites et chargement différé.

    `widths` : largeurs déclarées sur le modèle (ex. Institution.LOGO_WIDTHS).
    """
    if not field_file:
        return ""
    field, instance = field_file.field, field_file.instance
    width = getattr(instance, field.width_field, None) if field.width_field else None
    height = getattr(instance, field.height_field, None) if field.height_field else None
    available = rendition_widths(width, widths)
    if not available:
        return format_html('<img src="{}" alt="{}" class="{}">', field_file.url, alt, css_class)
    url = field_file.storage.url
    srcset = ", ".join(f"{url(rendition_name(field_file.name, w))} {w}w" for w in available)
    return format_html(
        '<img src="{}" srcset="{}" sizes="{}" width="{}" height="{}" alt="{}" class="{}" '
        'loading="{}" decoding="async">',
        url(rendition_name(field_file.name, available[-1])),
        srcset,
        sizes,
        width,
        height,
        alt,
        css_class,
        "eager" if eager else "lazy",
    )


@register.inclusion_tag("components/admin_bar.html", takes_context=True)
def admin_bar(context):
    """Raccourcis « Modifier » vers les pages de gestion de l'espace, pour les éditeurs et
    les administrateurs.

    Les vues listent dans `edit_targets` ce que montre la page : un objet mène à son
    formulaire, un modèle à sa liste. Seuls les éléments que l'utilisateur peut modifier
    apparaissent.
    """
    from apps.dashboard import manage  # le registre importe tous les modèles

    user = context.get("user")
    if user is None or not is_back_office(user):
        return {"links": None}
    links = []
    for target in context.get("edit_targets", ()):
        model = target if isinstance(target, type) else type(target)
        managed = manage.for_model(model)
        if managed is None or not may(user, "change", model):
            continue
        if isinstance(target, type):
            label, url = managed.title, managed.list_url()
        else:
            kind, name = capfirst(model._meta.verbose_name), str(target)
            label = kind
            if name.lower() != kind.lower():
                label = _("%(kind)s “%(name)s”") % {"kind": kind, "name": name}
            url = managed.edit_url(target)
        links.append((label, url))
    return {"links": links}


@register.filter
def verbose_name(obj):
    """Nom du type d'un objet : « Publication », « Jeu de données »…"""
    return capfirst(obj._meta.verbose_name)


@register.filter
def render_markdown(text):
    html = markdown_lib.markdown(text or "", extensions=["tables", "sane_lists"])
    return mark_safe(nh3.clean(html, tags=MARKDOWN_TAGS, link_rel="noopener"))
