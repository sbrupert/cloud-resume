import cloud_resume.markdown as markdown_utils


def test_markdown_renderer_sanitizes_unsafe_html():
    unsafe_markdown = """
## Sample
<script>alert("xss")</script>
<img src="x" onerror="alert(1)">
[bad](javascript:alert(1))
**safe text**
"""
    rendered = markdown_utils.render_markdown_safely(unsafe_markdown)
    assert "<script" not in rendered
    assert "javascript:" not in rendered
    assert '<img src="x">' in rendered
    assert "onerror=" not in rendered
    assert "<strong>safe text</strong>" in rendered


def test_markdown_renderer_supports_standard_image_links():
    markdown_text = "![standard](https://example.com/standard.png)\n\n![gif alt](https://example.com/standard.gif)"
    rendered = markdown_utils.render_markdown_safely(markdown_text)
    assert '<img alt="standard" src="https://example.com/standard.png">' in rendered
    assert '<img alt="gif alt" src="https://example.com/standard.gif">' in rendered


def test_markdown_renderer_wraps_toc_in_details():
    markdown_text = "[TOC]\n\n## Intro\n\n## Another Heading"
    rendered = markdown_utils.render_markdown_safely(markdown_text)
    assert "<details>" in rendered
    assert "<details open>" not in rendered
    assert "<summary>Table of Contents</summary>" in rendered
    assert '<div class="toc">' in rendered
