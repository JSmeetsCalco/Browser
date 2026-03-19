import socket
import ssl

class URL:
    def __init__(self, url):
        # Split schemes
        # Split HTTP(S) and file URLs
        if "://" in url:
            self.scheme, url = url.split("://", 1)
        # Split data URLs    
        else:
            self.scheme, url = url.split(":", 1)
        
        # Check that scheme is accepted by browser
        assert self.scheme in ["http", "https", "file", "data"]

        # --------------------------
        # DATA SCHEME (handle first)
        # --------------------------
        if self.scheme == "data":
            metadata, data = url.split(",", 1)
            # Default MIME type if none provided
            self.mediatype = metadata if metadata else "text/plain"
            self.data = data
            return
        
        # -----------
        # FILE SCHEME
        # -----------
        if self.scheme == "file":
            self.host = ""
            self.path = url[1:]
            return
        
        # -----------------------
        # HTTP / HTTPS ONLY BELOW
        # -----------------------
        
        # Normalize URL
        if "/" not in url:
            url += "/"
         # Split host and path
        self.host, url = url.split("/", 1)
        self.path = "/" + url

        # Default ports for HTTP and HTTPS
        if self.scheme == "http":
            self.port = 80
        elif self.scheme == "https":
            self.port = 443
        
        # Added support for custom ports (specified in URL by putting a colon after the host name)
        if ":" in self.host:
            self.host, port = self.host.split(":", 1)
            self.port = int(port)

    def request(self):
        # First check whether connection if file. If so, no socket needs to be created
        if self.scheme == "file":
            with open(self.path, "r", encoding="utf8") as f:
                return f.read()
        
        # Check whether connection is data scheme
        if self.scheme == "data":
            return self.data

        # Create the socket
        # Family tells you how to find the other computer
        # Type describes the sort of conversation that's going to happen (Stream = each computer can send arbitrary amounts of data)
        # Protocol descibres the steps by which the two computers will establish a connection
        s = socket.socket(
            family=socket.AF_INET,
            type=socket.SOCK_STREAM,
            proto=socket.IPPROTO_TCP
        )
        # Connects the socket to the other computer (host and port)
        s.connect((self.host, self.port))

        # If the site uses HTTPS, wrap the socket using the ssl library
        if self.scheme == "https":
            ctx = ssl.create_default_context()
            s = ctx.wrap_socket(s, server_hostname=self.host)

        # Defining headers to send with request
        headers = {
            "Host": self.host,
            "Connection": "close",
            "User-Agent": "JSBrowser"
        }
        
        # Makes a request to the other server, sending it data through the send method
        request = "GET {} HTTP/1.1\r\n".format(self.path)
        # Loops through all headers and adds data to request
        for header, value in headers.items():
            request += "{}: {}\r\n".format(header, value)
        request += "\r\n"
        s.send(request.encode("utf8"))
        # If you see an error about str versus bytes, it's because you forgot to call encode or decode somewhere

        # Read's the server's response
        response = s.makefile("r", encoding="utf8", newline="\r\n")

        # Splits that response into pieces
        statusline = response.readline()
        version, status, explanation = statusline.split(" ", 2)

        # After the status line come the headers:
        response_headers = {}
        while True:
            line = response.readline()
            # Break at the final blank line
            if line == "\r\n": break
            # Each line is split at the colon, and header names are mapped to header values
            header, value = line.split(":", 1)
            # Headers are case-insensitive, and whitespace is insignificant, so both are normalized here
            response_headers[header.casefold()] = value.strip()
        
        # Ensures data is sent correctly
        assert "transfer-encoding" not in response_headers
        assert "content-encoding" not in response_headers

        # The content is everything after the headers
        content = response.read()
        s.close()

        # Return the body, to be displayed
        return content

def show(body):
    # Prints only the actual text, not the tags of the HTML
    in_tag = False
    i = 0

    # Dictionary of supported entities
    entities = {
        "&lt;": "<",
        "&gt;": ">",
        "&amp;": "&",      # easy to add more
        "&quot;": "\""
    }

    while i < len(body):
        matched = False

        # Check if we're at the start of any known entity
        if body[i] == "&":
            semicolon = body.find(";", i)
            if semicolon != -1:
                entity = body[i:semicolon+1]
                if entity in entities:
                    print(entities[entity], end="")
                    i = semicolon + 1
                    continue

        if matched:
            continue

        c = body[i]

        if c == "<":
            in_tag = True
        elif c == ">":
            in_tag = False
        elif not in_tag:
            print(c, end="")

        i += 1

def load(url):
    # Loads web page based on URL.request and show()
    body = url.request()
    show(body)

if __name__ == "__main__":
    import sys

    # If program is started without URL given, load standard file
    if len(sys.argv) < 2:
        url = URL("file:///C:/CodingProjects/Browser/Debugging/file.html")
    else:
        url = URL(sys.argv[1])

    load(url)