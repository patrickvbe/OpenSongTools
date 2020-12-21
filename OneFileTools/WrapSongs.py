#! /usr/bin/env python3
import os
import xml.etree.ElementTree as ET
import math
from itertools import chain

class SongWrapper:
    def __init__(self, filename):
        self.filename = filename
        self.maxlinelen = 37
        self.maxlines = 7
        self.filechanged = False
        self.ignorebreaks = False

    def initlyrics(self):
        self.verse = []
        self.wrapped = ''

    def generate_line_parts(self, line):
        linelen = len(line)
        parts = math.ceil(linelen / self.maxlinelen)
        partlen = math.ceil(linelen / parts)
        start = 0
        end = partlen
        while end < linelen:
            if line[end].isspace():
                yield line[start:end]
                start = end
                end += linelen
            else:
                end += 1
        yield line[start:]

    def generate_sheets(self):
        lines = len(self.verse)
        sheets = math.ceil(lines / self.maxlines)
        linespersheet = math.ceil(lines / sheets)
        sheetline = 0
        for line in self.verse:
            if sheetline == linespersheet:
                yield ' ||'
                sheetline = 0
                self.filechanged = True
            yield line
            sheetline += 1

    def doverse(self):
        if len(self.verse) == 0:
            return
        self.wrapped += '\n'.join(self.generate_sheets())
        self.wrapped += '\n'
        self.verse = []

    def fixtext(self, text):
        linelen = len(text)
        text = text.replace(' / ', '\n ')
        text = text.replace(' !', '!')
        text = text.replace(' ?', '?')
        if linelen != len(text):
            self.filechanged = True
        return text

    def wrapsong(self):
        tree = ET.parse(self.filename)
        for element in chain(tree.iterfind('lyrics'), tree.iterfind('Lyrics')):
            self.initlyrics()
            for line in self.fixtext(element.text).splitlines():
                line = line.rstrip()
                linelen = len(line)
                if linelen > 0:
                    if line[0] == ' ' and (self.ignorebreaks or line != ' ||') :
                        if line[1:].isnumeric() or (self.ignorebreaks and line == ' ||'):
                            # Only one number on the line: probably the verse. Skipt it.
                            self.filechanged = True
                        else:
                            self.verse += self.generate_line_parts(line)
                    else:
                        self.doverse()
                        self.wrapped += line
                        self.wrapped += '\n'
            self.doverse()
            element.text = self.wrapped
        if self.filechanged:
            print(self.filename)
            tree.write(self.filename, encoding="UTF-8", xml_declaration=True)

for pathname in os.listdir('.'):
    if os.path.isfile(pathname):
        SongWrapper(pathname).wrapsong()
