from functools import total_ordering
import re
from dataclasses import dataclass
from pathlib import Path

import arrow
import markdown
import pymdownx.blocks.admonition
import pymdownx.bracketspan
import pymdownx.extra
import pymdownx.quotes
import pymdownx.superfences
from bs4 import BeautifulSoup, Comment
from bs4.formatter import HTMLFormatter

formatter = HTMLFormatter(indent=4)

# Get all HTML files that aren't the templates
current_file_path = Path(__file__).resolve()
site_directory = current_file_path.parent

now = arrow.now()

RE_MAIN = re.compile(r" *<main>.*<\/main>", re.DOTALL)
MONTHS = ["N/A", "January", "Feburary", "March", "April",
          "May", "June", "July", "August", "September",
          "October", "November", "December"]

md_extensions = [pymdownx.extra.ExtraExtension(),
                pymdownx.superfences.SuperFencesCodeExtension(),
                pymdownx.blocks.admonition.AdmonitionExtension(),
                pymdownx.bracketspan.BracketSpanExtension(),
                pymdownx.quotes.QuotesExtension()]

def indent(s: str, level = 0):
    lines = s.splitlines()
    new_lines = []
    in_a_code_block = False
    for l in lines:
        if not in_a_code_block:
            new_lines.append("    " * level + l)
        else:
            new_lines.append(l)

        if l.startswith("<pre"):
            in_a_code_block = True
        elif l.endswith("</pre>"):
            in_a_code_block = False

    return "\n".join(new_lines)

def strip_html(soup: BeautifulSoup) -> str:
    return soup.get_text(separator = " ", strip = True)

def strip_markdown(text: str) -> str:
    html = markdown.markdown(text)
    soup = BeautifulSoup(html, "html.parser")
    return strip_html(soup)

@total_ordering
@dataclass
class Post:
    url: str
    en_title: str
    tp_title: str
    year: str
    month: str
    day: str
    en_excerpt: str
    tp_excerpt: str

    def __lt__(self, other: "Post"):
        return (self.year, self.month, self.day, self.en_title) < (other.year, other.month, other.day, other.en_title)

posts: list[Post] = []

def generate_blog_posts():
    posts_en_directory = site_directory / "posts" / "en"
    posts_tp_directory = site_directory / "posts" / "tp"
    blog_directory = site_directory / "blog"

    all_posts = posts_en_directory.glob("*.md")
    for post in all_posts:
        print(f"Generating blog post {post.stem}")

        en_doc = post.read_text(encoding = "utf-8")
        en_html = markdown.markdown(en_doc, extensions = md_extensions, tab_length = 4)
        en_soup = BeautifulSoup(en_html, "html.parser")

        tp_path = posts_tp_directory / post.name
        if tp_path.exists():
            tp_doc = tp_path.read_text(encoding = "utf-8")
            tp_html = markdown.markdown(tp_doc, extensions = md_extensions, tab_length = 4)
        else:
            tp_path = site_directory / "templates" / "no_tp.html"
            tp_html = tp_path.read_text(encoding = "utf-8")
        tp_soup = BeautifulSoup(tp_html, "html.parser")

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
        new_path.write_text(out, encoding = "utf-8")

        en_title = en_soup.find("h1")
        tp_title = tp_soup.find("h1")

        if en_title:
            en_title_text = en_title.text
            en_title.decompose()
        else:
            en_title_text = "No Title"

        if tp_title:
            tp_title_text = tp_title.text
            tp_title.decompose()
        else:
            tp_title_text = "nimi ala"

        if tp_title_text == "toki&pona ala":
            tp_title_text = f"toki&pona ala <span class=\"sl smaller\">({en_title_text})</span>"

        en_excerpt = strip_html(en_soup).replace("\n", " ")[:256]
        tp_excerpt = strip_html(tp_soup).replace("\n", " ")[:256]

        year = post.stem[:4]
        month = post.stem[4:6]
        day = post.stem[6:8]

        posts.append(Post(f"/blog/{post.stem}.html", en_title_text, tp_title_text,
                          year, month, day, en_excerpt, tp_excerpt))

    posts.sort(reverse = True)

def make_post_page():
    template = site_directory / "templates" / "articles.html"
    template_doc = template.read_text(encoding = "utf-8")

    en_post_template = site_directory / "templates" / "en_blog_entry.html"
    en_post_template_doc = en_post_template.read_text(encoding = "utf-8")

    tp_post_template = site_directory / "templates" / "tp_blog_entry.html"
    tp_post_template_doc = tp_post_template.read_text(encoding = "utf-8")

    en_posts = []
    tp_posts = []

    for post in posts:
        en_replacements = {
            "$URL": post.url,
            "$POSTTITLE": post.en_title,
            "$PMM": MONTHS[int(post.month)],
            "$PDD": post.day,
            "$PYYYY": post.year,
            "$POSTEXCERPT": post.en_excerpt
        }

        tp_replacements = {
            "$URL": post.url,
            "$POSTTITLE": post.tp_title,
            "$PMM": post.month,
            "$PDD": post.day,
            "$PYYYY": post.year,
            "$POSTEXCERPT": post.tp_excerpt
        }

        en_post = en_post_template_doc
        tp_post = tp_post_template_doc

        for k, v in en_replacements.items():
            en_post = en_post.replace(k, v)

        for k, v in tp_replacements.items():
            tp_post = tp_post.replace(k, v)

        en_posts.append(en_post)
        tp_posts.append(tp_post)

    en_posts_string = "\n".join(en_posts)
    tp_posts_string = "\n".join(tp_posts)
    template_doc = template_doc.replace("$EN_ARTICLES", indent(en_posts_string, 2)).replace("$TP_ARTICLES", indent(tp_posts_string, 2))

    final_path = site_directory / "blog" / "index.html"
    final_path.write_text(indent(template_doc, 1), encoding = "utf-8")

def update_template():
    all_html_files = site_directory.glob("**/*.html")
    html_files = [h for h in all_html_files if h.parent.stem != "templates"]

    for page in html_files:
        doc = page.read_text(encoding = "utf-8")
        soup = BeautifulSoup(doc, 'html.parser')

        # Get top two comments
        # https://stackoverflow.com/questions/33138937/how-to-find-all-comments-with-beautiful-soup
        comments = soup.find_all(string=lambda text: isinstance(text, Comment))
        name = comments[0].strip()
        desc = comments[1].strip() if len(comments) > 1 else "No description is available for this page."

        print("Processing", name)

        # Get the templates

        head = site_directory / "templates" / "head.html"
        head_doc = head.read_text(encoding = "utf-8")

        header = site_directory / "templates" / "header.html"
        header_doc = header.read_text(encoding = "utf-8")

        footer = site_directory / "templates" / "footer.html"
        footer_doc = footer.read_text(encoding = "utf-8")

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

        page.write_text(out, encoding = "utf-8")

def main():
    generate_blog_posts()
    make_post_page()
    update_template()

if __name__ == "__main__":
    main()
