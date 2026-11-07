"""File per i motori di ricerca: sitemap.xml e robots.txt.

I meta tag (title, description, Open Graph, hreflang) sono in templates/partials/meta.html.
"""

from xml.sax.saxutils import quoteattr, escape


def sitemap_xml(pages: list[dict[str, str]]) -> str:
    """Una voce per ogni pagina in ogni lingua, con i link alle versioni nelle altre lingue.

    `pages` è un elenco di {lingua: URL assoluto}, una voce per pagina.
    """
    entries = []
    for versions in pages:
        alternates = "".join(
            f'\n    <xhtml:link rel="alternate" hreflang="{lang}" href={quoteattr(url)}/>'
            for lang, url in versions.items()
        )
        for url in versions.values():
            entries.append(f"  <url>\n    <loc>{escape(url)}</loc>{alternates}\n  </url>")
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
        'xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
        + "\n".join(entries)
        + "\n</urlset>\n"
    )


def robots_txt(sitemap_url: str) -> str:
    return f"User-agent: *\nAllow: /\n\nSitemap: {sitemap_url}\n"
