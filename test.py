phrase = "&ltHello&gt"

for i, c in enumerate(phrase):
    if c == "&":
        if phrase[i + 1] == "l" and phrase[i + 2] == "t":
            c = "<"
            i += 2
            continue
        elif phrase[i + 1] == "g" and phrase[i + 2] == "t":
            c = ">"
            i += 2
            continue
    print(c, end="")