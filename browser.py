import socket, ssl, os, base64, urllib
import urllib.parse

class URL:
    USER_AGENT = "Mozilla/5.0 (iPad; CPU iPad OS 9_5_0 like Mac OS X) AppleWebKit/600.39 (KHTML, like Gecko)  Chrome/52.0.3769.344 Mobile Safari/603.9"
    DATA_SCHEME_DEFAULT_MIME = "text/plain;charset=US-ASCII"

    def __init__(self, url):
        self.scheme = self.host = self.path = self.port = self.data_is_base64 = None   
        self.data_mediatype = self.data_raw_content = None
        self.data_is_base64 = False
        
        self.scheme, url = url.split(":", 1)
        assert self.scheme in [ "http" , "https", "file", "data", "view-source"]
        
        if self.scheme == "data":
            self._scheme_data_init(url)
            
        elif self.scheme in [ "http" , "https", "file"]:
            self._scheme_http_https_file_init(url)

    def _scheme_data_init(self, url):
        media_type_and_encoding, self.data_raw_content = url.split(",", 1)
        if not media_type_and_encoding:
            self.data_mediatype = self.DATA_SCHEME_DEFAULT_MIME
        else:
            if ";" in media_type_and_encoding:
                self.data_mediatype, base64_str = media_type_and_encoding.split(";", 1)

                if base64_str == "base64":
                    self.data_is_base64 = True
            else:
                self.data_mediatype = media_type_and_encoding
            if not self.data_mediatype:
                self.data_mediatype = self.DATA_SCHEME_DEFAULT_MIME
    
    def _scheme_http_https_file_init(self, url):
        if self.scheme in  ["http" , "https"]:
            url = url.lstrip("/")

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

     
    def set_headers(self, request, headers: dict):
        for key in headers:
            request += f"{key}: {headers[key]}\r\n"
        return request
    
    def file_urls(self, url_path):
        normalized_path = os.path.normpath(url_path)
        try:
            with open(normalized_path, "r") as file:
                text = file.read()
        except FileNotFoundError: 
            normalized_path = os.path.normpath("default.txt")
            with open(normalized_path, "r") as file:
                text = file.read()
        except Exception as e:
            print(f"Error reading file")
            return f"Error reading file: {e}"
        return text
    
    def inline_data_retrieve(self):
        if self.data_is_base64:
            try:
                base64_input = self.data_raw_content.encode()
                decoded_bytes = base64.b64decode(base64_input)

                charset = 'utf-8'
                if "charset=" in self.data_mediatype:
                    try:
                        charset_part = self.data_mediatype.split("charset=", 1)[1].split(";")[0]
                        charset = charset_part.strip()
                    except IndexError:
                        pass
                return decoded_bytes.decode(charset)
            except (base64.binascii.Error, UnicodeDecodeError) as e:
                print(f"Error decoding Base64 data: {e}")
                return f"Error: Could not decode data URL content ({e})"
        else:
            return urllib.parse.unquote(self.data_raw_content)


    def internet_request(self):
        try:
            s = socket.socket(
                family=socket.AF_INET,
                type=socket.SOCK_STREAM,
                proto=socket.IPPROTO_TCP
            )
            s.connect((self.host, self.port))
            
            headers = {
                "Host": self.host,
                "Connection": "close",
                "User-Agent": self.USER_AGENT
            }
            
            if self.scheme == "https":
                ctx  = ssl.create_default_context()
                s = ctx.wrap_socket(s, server_hostname=self.host)
            
            request = f"GET {self.path} HTTP/1.1\r\n"
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
        except Exception as e:
            print(f"Error sending internet request")
            return f"Error sending internet request: {e}" 
    
    def request(self):
        if self.scheme == "data":
            content = self.inline_data_retrieve() 
        elif self.scheme == "file":
            content = self.file_urls(self.path)
        elif self.scheme in ["http", "https"]:
            content = self.internet_request()
        return content
    
    def to_string(self):
        if self.scheme is not None:
            url_str = f"{self.scheme}://"
        
        if self.host is not None:
            url_str += self.host

        if self.port is not None:
            if not ((self.scheme == "http" and self.port == 80) or \
                    (self.scheme == "https" and self.port == 443)):
                url_str += f":{self.port}"

        if self.port is not None:        
            url_str += self.path

        return url_str


def show(body):
    in_tag = False
    entities = False
    entity_str = ""

    for c in body:
        if c == "<":
            in_tag = True
        elif c == ">":
            in_tag = False
        elif not in_tag:
            if c =="&":
                entities = True
            elif c ==";":
                entities = False
                entity_str += c
            if entities:
                entity_str += c
                continue
        
            if entity_str == "&lt;":
                entity_str=""
                print("<", end="")
            elif entity_str == "&gt;":
                entity_str=""
                print(">", end="")
            elif entity_str == "&copy;":
                entity_str=""
                print("©", end="")
            elif entity_str == "&amp;":
                entity_str=""
                print("&", end="")
            elif entity_str == "&ndash;":
                entity_str=""
                print("-", end="")
            elif not entities:
                print(c, end="")
            

def load(url:URL):
    content = url.request()
    show(content)


if __name__ == "__main__":
    import sys
    url_URL = URL(sys.argv[1])
    load(url_URL)