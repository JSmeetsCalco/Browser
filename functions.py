
WIDTH, HEIGHT = 800, 600
HSTEP, VSTEP = 13, 18
SCROLL_STEP = 100

def lex(body):
    text = ""
    in_tag = False

    for c in body:
        if c == "<":
            in_tag = True
        elif c == ">":
            in_tag = False
        elif not in_tag:
            text += c
    
    return text

def layout(text, width):
    display_list = []
    # Displaces cursor so not all text is printed in the same spot
    cursor_x, cursor_y = HSTEP, VSTEP

    # Loop through all characters in text to display and add them to list
    for c in text:
        # Handle new lines
        if c == "\n":
            cursor_x = HSTEP
            cursor_y += 2 * VSTEP
            continue

        display_list.append((cursor_x, cursor_y, c))
        # Go to next horizontal position
        cursor_x += HSTEP

        # Wrap to next line if you reach the end of the canvas
        if cursor_x >= width - HSTEP:
            cursor_y += VSTEP
            cursor_x = HSTEP
    
    return display_list