import socket, ssl

class URL:
    def __init__(self, url):
        self.user_agent = "Mozilla/5.0 (iPad; CPU iPad OS 9_5_0 like Mac OS X) AppleWebKit/600.39 (KHTML, like Gecko)  Chrome/52.0.3769.344 Mobile Safari/603.9"
        self.scheme, url = url.split("://", 1)
        assert self.scheme in [ "http" , "https", "file"]

        if "/" not in url:
            url += '/'
        self.host, url = url.split("/", 1)

        self.path = "/" + url 

        if ":" in self.host:
            self.host, port = self.host.split(":", 1)
            self.port = int(port)
        elif self.scheme == "http":
            self.port = 80
        elif self.scheme == "https":
            self.port = 443


    def file_urls(self, path):
        try:
            with open(path, "r") as file:
                text = file.read()
        except: 
            with open("default.txt", "r") as file:
                text = file.read()
        return text
    
    
    def set_headers(self, request, headers: dict):
        for key in headers:
            request += "{}: {}\r\n".format(key, headers[key])
        return request
    

    def internet_request(self):
        s = socket.socket(
            family=socket.AF_INET,
            type=socket.SOCK_STREAM,
            proto=socket.IPPROTO_TCP
        )
        s.connect((self.host, self.port))
        
        headers = {
            "Host": self.host,
            "Connection": "close",
            "User-Agent": self.user_agent
        }
        
        if self.scheme == "https":
            ctx  = ssl.create_default_context()
            s = ctx.wrap_socket(s, server_hostname=self.host)
        
        request = "GET {} HTTP/1.1\r\n".format(self.path)
        request = self.set_headers(request=request, headers=headers)
        request += "\r\n"

        s.send(request.encode("utf8"))

        response = s.makefile("r", encoding="utf8", newline="\r\n")
        statusline = response.readline()
        version, status, explanation = statusline.split(" ", 2)
        response_headers = {}
        while True:
            line = response.readline()
            if line == "\r\n": break
            header, value  = line.split(":", 1)
            response_headers[header.casefold()] = value.strip()
    
        assert "transfer-encoding" not in response_headers
        assert "content-encoding" not in response_headers
        content = response.read()
        s.close()
        return content
    
    def request(self):
        if self.scheme == "file":
            content = self.file_urls(self.path)
        elif self.scheme in ["http", "https"]:
            content = self.internet_request()
        return content
    
def show(body):
    in_tag = False
    for c in body:
        if c == "<":
            in_tag = True
        elif c == ">":
            in_tag = False
        elif not in_tag:
            print(c, end="")

def load(url):
    content = url.request()
    show(content)


if __name__ == "__main__":
    import sys
    load(URL(sys.argv[1]))