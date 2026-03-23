import os
import tkinter
from url import URL
from functions import lex, layout, WIDTH, HEIGHT, VSTEP, HSTEP, SCROLL_STEP



class Browser:
    def __init__(self):
        self.window = tkinter.Tk()
        self.canvas = tkinter.Canvas(
            self.window,
            width=WIDTH,
            height=HEIGHT
        )
        self.canvas.pack(fill="both", expand=True)
        self.scroll = 0
        self.width = WIDTH
        self.height = HEIGHT

        # Store images, otherwise they disappear
        self.images = {}

        # Bind down arrow to scroll down function
        self.window.bind("<Down>", self.scrolldown)

        # Bind up arrow to scroll up function
        self.window.bind("<Up>", self.scrollup)

        # Bind mousewheel to scrolling
        self.window.bind("<MouseWheel>", self.on_mousewheel)

        # Bind resize event
        self.window.bind("<Configure>", self.resize)
    
    def load(self, url):
        # Loads web page based on URL.request() and show()
        body = url.request()
        self.text = lex(body)
        self.display_list = layout(self.text, self.width)
        self.draw()

    def draw(self):
        # Delete the previous canvas layout to allow scrolling without text printed over each other
        self.canvas.delete("all")

        # Draw text
        for x, y, c in self.display_list:
            # Skip drawing characters that are offscreen
            if y > self.scroll + self.height: continue
            if y + VSTEP < self.scroll: continue
            
            # Check whether character is an emoji
            emoji = self.get_emoji(c)

            if emoji:
                self.canvas.create_image(x, y - self.scroll, image=emoji, anchor="center")
            else:
                # Print characters that are onscreen
                self.canvas.create_text(x, y - self.scroll, text=c)
        
        # Scrollbar logic
        if not self.display_list:
            return
        
        max_y = max(y for x, y, c in self.display_list)

        # Hide scrollbar if everything fits
        if max_y <= self.height:
            return
        
        # Compute scrollbar size
        bar_height = self.height * (self.height / max_y)

        # Compute scrollbar position
        max_scroll = max_y - self.height

        if max_scroll == 0:
            bar_top = 0
        else:
            bar_top = (self.scroll / max_scroll) * (self.height - bar_height)

        # Draw scrollbar
        self.canvas.create_rectangle(
            self.width - 12,
            bar_top,
            self.width - 4,
            bar_top + bar_height,
            fill="blue",
            outline="black"
        )
    
    def scrolldown(self, event):
        self.scroll += SCROLL_STEP
        self.clamp_scroll()
        self.draw()
    
    def scrollup(self, event):
        # Scroll down by scroll step
        self.scroll -= SCROLL_STEP
        self.clamp_scroll()
        self.draw()
    
    def on_mousewheel(self, event):
        # Scroll up or down depending on mousewheel
        if event.delta > 0:
            self.scroll -= SCROLL_STEP
        else:
            self.scroll += SCROLL_STEP
        
        self.clamp_scroll()
        
        self.draw()
    
    def clamp_scroll(self):
        if not self.display_list:
            return
        
        max_y = max(y for x, y, c in self.display_list)
        max_scroll = max(0, max_y - self.height)

        if self.scroll < 0:
            self.scroll = 0
        elif self.scroll > max_scroll:
            self.scroll = max_scroll
    
    def resize(self, event):
        self.width = event.width
        self.height = event.height

        # Recompute layout if content exists
        if hasattr(self, "text"):
            self.display_list = layout(self.text, self.width)
            self.draw()

    def get_emoji(self, char):
        # Convert unicode to hexcode
        codepoint = f"{ord(char):X}"

        # Add codepoint to images cache if not in there already
        if codepoint not in self.images:
            # Path to file
            filename = f"Emojis/{codepoint}.png"

            # Convert image to Tkinter image
            if os.path.exists(filename):
                self.images[codepoint] = tkinter.PhotoImage(file=filename)
            else:
                return None
        
        # Return image from cache
        return self.images[codepoint]


if __name__ == "__main__":
    import sys
    Browser().load(URL(sys.argv[1]))
    tkinter.mainloop()