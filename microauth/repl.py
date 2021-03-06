#!/usr/bin/env python
import cmd
import json
import pprint
import optparse
from microauth.client import Client
from microauth.models import APIKey
from microauth.utils  import spaceparse

try:
    from pygments import highlight
    from pygments.lexers import JSONLexer
    from pygments.styles import get_style_by_name, STYLE_MAP
    from pygments.formatters.terminal256 import Terminal256Formatter
except ImportError: highlight = False

def suppress_unicode_repr(object, context, maxlevels, level):
    typ = pprint._type(object)
    if typ is unicode:
        object = str(object)
    return pprint._safe_repr(object, context, maxlevels, level)

class repl(cmd.Cmd):

    prompt = "> "        
    intro = "Microauth repl."
    ruler = '-'
    printer = pprint.PrettyPrinter()
    printer.format = suppress_unicode_repr

    def parse_args(self, args):
        body = {}
        parsed = spaceparse(args)
        args = args.split()
        for i in args:
            try:
                x=i.split('=')
                if isinstance(parsed, dict) and not x[0] in parsed:
                    parsed[x[0]] = x[1]
                else:
                    body[x[0]] = x[1]
            except: continue
        if isinstance(parsed, dict):
            body = parsed
        return body

    def do_setkey(self,key):
        if key:
            self.c.key = key
            print('Changed active API key to "%s"' % key)
        else:
            print("Usage: setkey <key>")

    def do_use(self,key):
        "Alias of setkey."
        self.do_setkey(key)

    def do_getkey(self,line):
        print(self.c.key)

    def do_get(self,line):
        response = self.c._send_request(line)
        self.display(response)

    def do_put(self,line):
        line, body = line.split(' ',1)
        body = self.parse_args(body)
        response = self.c._send_request(line, 'PUT', body)
        self.display(response)

    def do_post(self,line):
        line, body = line.split(' ',1)
        body = self.parse_args(body)
        response = self.c._send_request(line, 'POST', body)
        self.display(response)

    def do_delete(self,line):
        if ' ' in line:
            line, body = line.split(' ',1)
            body = self.parse_args(body)
        else: body = ''
        response = self.c._send_request(line, 'DELETE', body)
        self.display(response)

    def do_EOF(self,line):
        return True

    def postloop(self):
        print

    def do_style(self, style):
        if not self.highlight:
            print("For syntax highlighting you will need to install the Pygments package.")
            print("sudo pip install pygments")
            return
        if style:
            self.style = style
            print('Changed style to "%s"' % style)
        else:
            print(', '.join(self.AVAILABLE_STYLES))
            print('Currently using "%s"' % self.style)

    def display(self, response):
        if self.highlight:
            print(response[1])
            print(highlight(json.dumps(response[0],indent=4), JSONLexer(), Terminal256Formatter(style=self.style)))
        else:
            print(self.printer.pprint(response))

def reqwrap(func):
    def wrapper(*args, **kwargs):
        try: return func(*args, **kwargs)
        except: return ({'error':'Connection refused.'}, 000)
    return wrapper

if __name__ == "__main__":
    parser = optparse.OptionParser(prog="python -m microauth.run")
    parser.add_option("--host", dest="host", action="store", default='localhost:7789/v1/')
    (options,args) = parser.parse_args()

    r = repl()
    r.c = Client('','https://%s' % options.host)

    r.c.key = ""
    k = APIKey.query.first()
    if k: r.c.key = k.key
    r.c.verify_https = False
    r.highlight = highlight
    if highlight:
        r.AVAILABLE_STYLES = set(STYLE_MAP.keys())
        if 'tango' in r.AVAILABLE_STYLES: r.style = 'tango'
        else:
            for s in r.AVAILABLE_STYLES: break
            r.style = s
    r.c._send_request = reqwrap(r.c._send_request)
    r.cmdloop()
