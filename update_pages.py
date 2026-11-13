import re
from pathlib import Path
from textwrap import dedent

import arrow
import markdown
import pymdownx.blocks.admonition
import pymdownx.extra
import pymdownx.superfences
from bs4 import BeautifulSoup, Comment
from bs4.formatter import HTMLFormatter

formatter = HTMLFormatter(indent=4)

# Get all HTML files that aren't the templates
current_file_path = Path(__file__).resolve()
site_directory = current_file_path.parent

now = arrow.now()

RE_MAIN = re.compile(r" *<main>.*<\/main>", re.DOTALL)

def indent(s: str, level = 0):
    lines = s.splitlines()
    new_lines = []
    for l in lines:
        new_lines.append("    " * level + l)
    return "\n".join(new_lines)

def generate_blog_posts():
    posts_en_directory = site_directory / "posts" / "en"
    posts_tp_directory = site_directory / "posts" / "tp"
    blog_directory = site_directory / "blog"

    all_posts = posts_en_directory.glob("*.md")
    for post in all_posts:
        en_doc = post.read_text()
        en_html = markdown.markdown(en_doc,
                                 extensions = [pymdownx.extra.ExtraExtension(),
                                               pymdownx.superfences.SuperFencesCodeExtension(),
                                               pymdownx.blocks.admonition.AdmonitionExtension()],
                                 tab_length = 4)

        tp_path = posts_tp_directory / post.name
        if tp_path.exists():
            tp_doc = tp_path.read_text()
            tp_html = markdown.markdown(tp_doc,
                                        extensions = [pymdownx.extra.ExtraExtension(),
                                                    pymdownx.superfences.SuperFencesCodeExtension(),
                                                    pymdownx.blocks.admonition.AdmonitionExtension()],
                                        tab_length = 4)
        else:
            tp_path = site_directory / "templates" / "no_tp.html"
            tp_html = tp_path.read_text()

        out = (f"<!--{post.stem}-->\n"
         "    <main>\n"
         "        <div class=\"lang-en\">\n") +\
                      indent(en_html, 3) + "\n" +\
        ("        </div>\n"
         "        <div class=\"lang-tp sp\">\n") +\
                      indent(tp_html, 3) + "\n" +\
        ("        </div>\n"
         "    </main>\n"
        )

        new_path = blog_directory / (post.stem + ".html")
        new_path.write_text(out)

def update_template():
    all_html_files = site_directory.glob("**/*.html")
    html_files = [h for h in all_html_files if h.parent.stem != "templates"]

    for page in html_files:
        doc = page.read_text()
        soup = BeautifulSoup(doc, 'html.parser')

        # Get top two comments
        # https://stackoverflow.com/questions/33138937/how-to-find-all-comments-with-beautiful-soup
        comments = soup.find_all(string=lambda text: isinstance(text, Comment))
        name = comments[0].strip()
        desc = comments[1].strip() if len(comments) > 1 else "No description is available for this page."

        print("Processing", name)

        # Get the templates

        head = site_directory / "templates" / "head.html"
        head_doc = head.read_text()

        header = site_directory / "templates" / "header.html"
        header_doc = header.read_text()

        footer = site_directory / "templates" / "footer.html"
        footer_doc = footer.read_text()

        # Replacements
        replacements = {
            "$NAME": name,
            "$DESC": desc,
            "$MM": now.format("MM"),
            "$DD": now.format("DD"),
            "$YYYY": now.format("YYYY")
        }

        main_match = re.search(RE_MAIN, doc)
        if not main_match:
            print("No main found!")
            continue

        main_text = main_match.group(0)

        out = "<!--$NAME-->\n<!--$DESC-->\n"
        out += head_doc
        out += "<body>\n"
        out += indent(header_doc, 1)
        out += "\n"
        out += main_text + "\n"
        out += indent(footer_doc, 1)
        out += "\n"
        out += indent("</body>", 1)
        out += "\n"
        out += "</html>\n"

        for rk, rv in replacements.items():
            out = out.replace(rk, rv)

        page.write_text(out)

def main():
    generate_blog_posts()
    update_template()

if __name__ == "__main__":
    main()
