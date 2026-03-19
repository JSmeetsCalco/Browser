import gzip
import io
import socket
import ssl
import time


#-------
# CACHES
#-------
# Cache to store socket connections for multiple use
connections = {}

# Cache for HTTP responses to reduce multiple downloads
cache = {}

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
        assert self.scheme in ["http", "https", "file", "data", "view-source"]

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
        
        # ------------------
        # VIEW-SOURCE SCHEME
        # ------------------
        if self.scheme == "view-source":
            # Store the inner URL as a new URL object
            self.inner_url = URL(url)
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

    def request(self, redirects=0):
        #---------
        # REDIRECT
        # --------

        # Only allow for 5 redirects before giving up on connection
        if redirects > 5:
            raise Exception("Too many redirects")
        
        # -------------
        # DEF CACHE KEY
        # -------------

        key = (self.scheme, self.host, self.port, self.path)
        
        # ------------
        # SCHEME CHECK
        # ------------

        # First check whether connection if file. If so, no socket needs to be created
        if self.scheme == "file":
            with open(self.path, "r", encoding="utf8") as f:
                return f.read()
        
        # Check whether connection is data scheme
        if self.scheme == "data":
            return self.data
        
        # Check whether scheme is View-Source
        if self.scheme == "view-source":
            return self.inner_url.request()
        
        # ------------
        # CHECK CACHES
        # ------------
        if key in cache:
            entry = cache[key]
            if entry["expires"] is None or entry["expires"] > time.time():
                return entry["body"]
            else:
                # Expired
                del cache[key]

        # Create key to be able to store socket connections
        key = (self.host, self.port)

        # Reload key if it is already in connections
        if key in connections:
            s = connections[key]

        # -------------
        # CREATE SOCKET
        # -------------

        else:
            # Create the socket (family = how to find other computer; type = what kind of connection (stream = each computer can send arbitrary amounts of data)
            # Protocol = describes steps by which teh two computers will establish a connection)
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

            # Store connection in connections cache
            connections[key] = s

        # --------------------
        # REQUEST AND RESPONSE
        # --------------------

        # Defining headers to send with request
        headers = {
            "Host": self.host,
            "Connection": "keep-alive",
            "User-Agent": "JSBrowser",
            "Accept-Encoding": "gzip"
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
        response = s.makefile("rb")

        # Splits that response into pieces
        statusline = response.readline().decode("utf8")
        version, status, explanation = statusline.split(" ", 2)

        # ----------------
        # RESPONSE HEADERS
        # ----------------

        # After the status line come the headers:
        response_headers = {}

        while True:
            line = response.readline().decode("utf8")
            # Break at the final blank line
            if line == "\r\n": break
            # Each line is split at the colon, and header names are mapped to header values
            header, value = line.split(":", 1)
            # Headers are case-insensitive, and whitespace is insignificant, so both are normalized here
            response_headers[header.casefold()] = value.strip()

        # ---------
        # REDIRECTS
        # ---------

        # Check for redirect code (3xx) in status
        if status.startswith("3"):
            # Redirect should always come with a redirect location. Get that location from the response_headers
            location = response_headers.get("location")

            # Check for if location header is missing
            if not location:
                raise Exception("Redirect without Location header")
            
            # Handle relative URLs
            if location.startswith("/"):
                location = f"{self.scheme}://{self.host}{location}"
            
            # Follow redirect
            new_url = URL(location)
            return new_url.request(redirects + 1)
        
        # ----------------
        # READ BODY
        # ----------------

        # Check for chunked encoding
        if response_headers.get("transfer-encoding") == "chunked":
            # The 'b' turns it into a byte string
            content = b""

            while True:
                # Read chunk size (hex)
                line = response.readline().decode("utf8").strip()
                chunk_size = int(line, 16)

                if chunk_size == 0:
                    # Consume final CRLF
                    response.readline()
                    break
                
                chunk = response.read(chunk_size)
                content += chunk

                # Consume CRLF after chunk
                response.readline()
        else:
            # Read content
            length = int(response_headers.get("content-length", 0))
            content = response.read(length)

        # Decompress if needed
        if response_headers.get("content-encoding") == "gzip":
            buf = io.BytesIO(content)
            f = gzip.GzipFile(fileobj=buf)
            content = f.read()

        # -------------
        # CACHE-CONTROL
        # -------------
        cache_control = response_headers.get("cache-control", "")

        should_cache = False
        expiry = None

        # Check whether content should be cached
        if status in ["200", "301", "404"]:
            if "no-store" in cache_control:
                should_cache = False
            elif "max-age" in cache_control:
                try:
                    max_age = int(cache_control.split("max-age=")[1].split(",")[0])
                    expiry = time.time() + max_age
                    should_cache = True
                except:
                    pass
            elif cache_control == "":
                should_cache = True
                expiry = None

        # Store cache
        decoded = content.decode("utf8")

        if should_cache:
            cache[key] = {
                "body": decoded,
                "expires": expiry
            }
        
        # Return body to be displayed
        return decoded

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

    # Loops through the length of the body text per character
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

    if url.scheme == "view-source":
        print(body)
    else:
        show(body)

if __name__ == "__main__":
    import sys

    # If program is started without URL given, load standard file
    if len(sys.argv) < 2:
        url = URL("file:///C:/CodingProjects/Browser/Debugging/file.html")
    else:
        url = URL(sys.argv[1])

    load(url)