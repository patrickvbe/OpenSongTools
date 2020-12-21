#! /usr/bin/env python3
# To get all you need:
# sudo apt-get install xclip (linux only)
# sudo pip3 install pyperclip
# sudo pip3 install inotify
import argparse
import os.path
import re
import subprocess
import pyperclip
import inotify.adapters

def ReformatLilyPond(text):
    # Replace some stuff we don't need with nothing.
    text = text.replace(r"\numericTimeSignature", "")
    text = text.replace(r"\break", "")
    text = re.sub(r"\\barNumberCheck #\d+", "", text)

    # process all lines. Remove comments and bar-checks, and fill them out
    # to 40 charactes per line. Lines starting with \ or } remain on their own line.
    result = ""
    linelen = 0
    for line in text.splitlines():
        commentstart = line.find('%')
        if commentstart >= 0:
            line = line[:commentstart]
        line = " ".join(line.replace('|', '').split())
        if line:
            if line[0] in '\\}':
                if linelen > 0:
                    result += '\n'
                result += line + '\n'
                linelen = 0
            elif linelen > 40:
                result += '\n' + line
                linelen = len(line)
            else:
                if linelen > 0:
                    result += ' '
                    linelen += 1
                linelen += len(line)
                result += line
    return result

# Command line arguments
parser = argparse.ArgumentParser(description='Watch a folder from .mscz and .xml (musicxml) files and when files change, convert them to LilyPond format and copy the notes to the clipboard.')
parser.add_argument('folder', help='The folder to watch')
parser.add_argument('-c', '--clipboard', action='store_true', help='Instead of printing the results, paste them to the clipboard')
parser.add_argument('-r', '--reformat', action='store_true', help='Reformat the notes section (strip comments, etc)')
parser.add_argument('-d', '--delete-xml-ly', action='store_true', help='Delete .xml and .ly files after processing')
args = parser.parse_args()

reg = re.compile(r'\\relative\s+[^{]*\{[^}]*\}')
watcher = inotify.adapters.Inotify()
watcher.add_watch(args.folder.encode(), inotify.constants.IN_CLOSE_WRITE + inotify.constants.IN_MOVED_TO)
for event in watcher.event_gen():
    try:
        if event is not None:
            header, type_names, watch_path, filename = event
            fullpath  = os.path.join(watch_path.decode(), filename.decode())
            root, ext = os.path.splitext(fullpath)
            if ext == '.mscz':
                subprocess.call(['musescore', '-o', root + '.xml', fullpath])
            elif ext == '.xml':
                subprocess.call(['musicxml2ly', '-l nederlands', '-o', root + '.ly', fullpath])
                if args.delete_xml_ly:
                    os.remove(fullpath)
            elif ext == '.ly':
                with open(fullpath) as file: 
                    match = reg.search(file.read())
                    if match:
                        text = ReformatLilyPond(match.group()) if args.reformat else match.group()
                        if args.clipboard:
                            pyperclip.copy(text)
                        else:
                            print(text)
                if args.delete_xml_ly:
                    os.remove(fullpath)
    except Exception as ex:
        print(ex)
