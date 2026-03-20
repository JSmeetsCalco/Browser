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
        self.canvas.pack()
        self.scroll = 0

        # Bind down arrow to scroll down function
        self.window.bind("<Down>", self.scrolldown)

        # Bind up arrow to scroll up function
        self.window.bind("<Up>", self.scrollup)

        # Bind mousewheel to scrolling
        self.window.bind("<MouseWheel>", self.on_mousewheel)
    
    def load(self, url):
        # Loads web page based on URL.request() and show()
        body = url.request()
        text = lex(body)
        self.display_list = layout(text)
        self.draw()

    def draw(self):
        # Delete the previous canvas layout to allow scrolling without text printed over each other
        self.canvas.delete("all")

        for x, y, c in self.display_list:
            # Skip drawing characters that are offscreen
            if y > self.scroll + HEIGHT: continue
            if y + VSTEP < self.scroll: continue
            
            # Print characters that are onscreen
            self.canvas.create_text(x, y - self.scroll, text=c)
    
    def scrolldown(self, event):
        self.scroll += SCROLL_STEP
        self.draw()
    
    def scrollup(self, event):
        # Scroll down by scroll step
        self.scroll -= SCROLL_STEP

        # Stop scrolling at the beginning of page
        if self.scroll < 0:
            self.scroll = 0
        
        self.draw()
    
    def on_mousewheel(self, event):
        # Scroll up or down depending on mousewheel
        if event.delta > 0:
            self.scroll -= SCROLL_STEP
        else:
            self.scroll += SCROLL_STEP
        
        # Stop scrolling up at top of page
        if self.scroll < 0:
            self.scroll = 0
        
        self.draw()

if __name__ == "__main__":
    import sys
    Browser().load(URL(sys.argv[1]))
    tkinter.mainloop()