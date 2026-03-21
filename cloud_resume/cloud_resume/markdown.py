import re
import nh3
from markdown import markdown

MARKDOWN_EXTENSIONS = ["codehilite", "fenced_code", "tables", "toc", "sane_lists"]
MARKDOWN_EXTENSION_CONFIGS = {
    "codehilite": {"guess_lang": "False", "linenums": "False"},
    "toc": {"toc_depth": "2-3", "permalink": "#", "permalink_title": "Permalink"},
}

ALLOWED_TAGS = set(nh3.ALLOWED_TAGS) | {
    "details",
    "div",
    "p",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "pre",
    "table",
    "thead",
    "tbody",
    "tr",
    "th",
    "td",
    "summary",
    "hr",
    "img",
}
ALLOWED_ATTRIBUTES = {
    **{tag: set(attrs) for tag, attrs in nh3.ALLOWED_ATTRIBUTES.items()},
    "a": {"href", "title", "rel"},
    "details": {"open"},
    "div": {"class"},
    "h1": {"id"},
    "h2": {"id"},
    "h3": {"id"},
    "h4": {"id"},
    "h5": {"id"},
    "h6": {"id"},
    "img": {"src", "alt", "title", "width", "height", "loading"},
    "code": {"class"},
    "pre": {"class"},
    "summary": {"class"},
    "th": {"colspan", "rowspan", "align"},
    "td": {"colspan", "rowspan", "align"},
}
ALLOWED_URL_SCHEMES = set(nh3.ALLOWED_URL_SCHEMES) | {"tel"}

sanitizer = nh3.Cleaner(
    tags=ALLOWED_TAGS,
    attributes=ALLOWED_ATTRIBUTES,
    clean_content_tags={"script", "style"},
    url_schemes=ALLOWED_URL_SCHEMES,
    link_rel=None,
)


def render_markdown_safely(text, flatpages=None, page=None):
    rendered_html = markdown(
        text,
        extensions=MARKDOWN_EXTENSIONS,
        extension_configs=MARKDOWN_EXTENSION_CONFIGS,
    )
    rendered_html = re.sub(
        r'(<div class="toc">.*?</div>)',
        r'<details><summary>Table of Contents</summary>\1</details>',
        rendered_html,
        count=1,
        flags=re.DOTALL,
    )
    return sanitizer.clean(rendered_html)
