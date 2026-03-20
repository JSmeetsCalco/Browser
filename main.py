from url import URL

if __name__ == "__main__":
    import sys

    # If program is started without URL given, load standard file
    if len(sys.argv) < 2:
        url = URL("file:///C:/CodingProjects/Browser/Debugging/file.html")
    else:
        url = URL(sys.argv[1])

    load(url)