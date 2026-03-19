phrase = "<body>You forgot to add a &ltURL&gt to the program call!</body>"

for i, c in enumerate(phrase):
    if c == "&":
        if phrase[i + 1] == "l" and phrase[i + 2] == "t":
            c = "<"
            i += 2
        elif phrase[i + 1] == "g" and phrase[i + 2] == "t":
            c = ">"
            i += 2
    print(c, end="")