from qqutils.stringutils import print_html, print_markdown


def test_print_markdown():
    print_markdown("# Hello, World!", justify="center")


def test_print_html():
    print_html("<p>Hello, World!</p>")
    print_html("<p>Hello, World!</p>", style="white on blue")
    print_html("<h1>Hello, World!</h1>")
    print_html("<p>Hello, Shanghai!</p>", width=10)
