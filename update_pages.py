import re
from pathlib import Path

import arrow
from bs4 import BeautifulSoup, Comment
from bs4.formatter import HTMLFormatter

formatter = HTMLFormatter(indent=4, )

# Get all HTML files that aren't the templates
current_file_path = Path(__file__).resolve()
site_directory = current_file_path.parent
all_html_files = site_directory.glob("**/*.html")
html_files = [h for h in all_html_files if h.parent.stem != "templates"]

now = arrow.now()

RE_MAIN = re.compile(r" *<main>.*<\/main>", re.DOTALL)

def indent(s: str, level = 0):
    lines = s.splitlines()
    new_lines = []
    for l in lines:
        new_lines.append("    " * level + l)
    return "\n".join(new_lines)

for page in html_files:
    doc = page.read_text()
    soup = BeautifulSoup(doc, 'html.parser')

    # Get top two comments
    # https://stackoverflow.com/questions/33138937/how-to-find-all-comments-with-beautiful-soup
    comments = soup.find_all(string=lambda text: isinstance(text, Comment))
    name = comments[0].strip()
    desc = comments[1].strip()

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
        "$YYYY": now.format("YY")
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
