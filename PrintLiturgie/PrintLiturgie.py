#! /usr/bin/env python3
from OpenSong.Presentation import *
from OpenSong.Song import *
from string import Template
import argparse
import os.path
import sys
from functools import reduce

filter = ['Liturgie']

default_set_template = '''<html>
<h1>Liturgie voor $name</h1>
$slidegroups
</html>'''
default_custom_slidegroup_template = '''
<h2>$title</h2>
$slides
'''
default_custom_slide_template = '''
<p>$body</p>
'''
default_scripture_slidegroup_template = '''
<h2>Schriftlezing</h2>
<h3>$title</h3>
<p>$slides</p>
'''
default_scripture_slide_template = '''
$body
'''
default_song_slidegroup_template = '''
<h2>$name</h2>
<table cellpadding=6>
$verses
</table>
'''
default_song_verse_template = '''
<tr><td valign="top">$versenr</td><td>$lyrics</td></tr>
'''

# songSlideGroupTemplate = Template('''
# <h2>$name</h2>
# $verses
# ''')

# songVerseTemplate = Template('''
# <p>$versenr</p>
# <p>$lyrics</p>
# ''')

# Command line arguments
parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                                 description='Print een liturgie op basis van een OpenSong presentatie.')
parser.add_argument('presentation', nargs='+', help='presentatie files')
parser.add_argument('--songroot',                                                                   help='OpenSong Song folder')
parser.add_argument('--destination',                 default='.',                                   help='Pad voor de uitvoer bestanden')
parser.add_argument('--extension',                   default='html',                                help='File extensie voor de liturgie file')
parser.add_argument('--settemplate',                 default=default_set_template,                  help='Template voor de set. Gebruik $name, $slidegroups')
parser.add_argument('--customslidegrouptemplate',    default=default_custom_slidegroup_template,    help='Template voor de text slide groep. Gebruik $name, $title, $subtitle, $slides')
parser.add_argument('--customslidetemplate',         default=default_custom_slide_template,         help='Template voor een text slide. Gebruik $body')
parser.add_argument('--scriptureslidegrouptemplate', default=default_scripture_slidegroup_template, help='Template voor de schriftlezing groep. Gebruik $name, $title, $subtitle, $slides')
parser.add_argument('--scriptureslidetemplate',      default=default_scripture_slide_template,      help='Template voor een schriftlezing slide. Gebruik $body')
parser.add_argument('--songslidegrouptemplate',      default=default_song_slidegroup_template,      help='Template voor de een lied. Gebruik $name, $verses')
parser.add_argument('--songversetemplate',           default=default_song_verse_template,           help='Template voor de een lied vers. Gebruik $versenr, $lyrics')
args = parser.parse_args()

setTemplate                 = Template(args.settemplate)
customSlideGroupTemplate    = Template(args.customslidegrouptemplate)
customslideTemplate         = Template(args.customslidetemplate)
scriptureSlideGroupTemplate = Template(args.scriptureslidegrouptemplate)
scriptureslideTemplate      = Template(args.scriptureslidetemplate)
songSlideGroupTemplate      = Template(args.songslidegrouptemplate)
songVerseTemplate           = Template(args.songversetemplate)

def FormatSlides(template, slides):
    formatted = ''
    for slide in slides:
        if slide.body and not slide.body.startswith('♫'):
            formatted += template.safe_substitute(body=slide.body.replace('\n', '<br>\n'))
    return formatted

def FormatVerses(song, present):
    result = ''
    if not present:
        present = song.present if song.present else sorted(list(song.verses.keys()))
    for verse in present:
        lyrics = song.verses.get(verse)
        if lyrics:
            versenr = verse.strip("V")
            if versenr.startswith("C"):
                versenr = "Refrein:"
            result += songVerseTemplate.safe_substitute(versenr=versenr,
                lyrics = reduce(lambda a, kv: a.replace(*kv), 
                         (('\n', '<br>\n'), (' _ ',' ')), "".join(lyrics)) )
    return result

def LoadSong(path, name):
    song = Song(os.path.join(args.songroot, path, name))
    try:
        song.Load()
    except Exception as ex:
        print("Failed to load song {0}: {1}".format(song.filename, str(ex)), file=sys.stderr)
        return None
    return song


def ConvertSong(songfile):
    set = OpenSongSet(songfile)
    try:
        set.Load()
    except Exception as ex:
        print(F"Failed to load presentation {songfile}: {str(ex)}", file=sys.stderr)
        return
    slidegroups = []
    for slide_group in set.slide_groups:
        slidetype = type(slide_group)
        if slidetype == SlideGroupScripture:
            slidegroups.append(scriptureSlideGroupTemplate.safe_substitute(name=slide_group.name,
                title  = slide_group.title, subtitle = slide_group.subtitle,
                slides = FormatSlides(scriptureslideTemplate, slide_group.slides)))
        elif slidetype == SlideGroupCustom:
            slidegroups.append(customSlideGroupTemplate.safe_substitute(name=slide_group.name,
                title    = slide_group.title if slide_group.title and slide_group.title != 'Liturgie' else slide_group.name,
                subtitle = slide_group.subtitle,
                slides   = FormatSlides(customslideTemplate, slide_group.slides)))
        elif slidetype == SlideGroupSong:
            song = LoadSong(slide_group.path, slide_group.name)
            if song:
                slidegroups.append(songSlideGroupTemplate.safe_substitute(name=slide_group.name,
                    verses=FormatVerses(song, slide_group.present)))
        elif slidetype == SlideGroupExternal:
            slidegroups.append(songSlideGroupTemplate.safe_substitute(name=slide_group.name, verses=""))
    with open(os.path.join(args.destination, songfile + '.' + args.extension), 'w') as outfile:
        print(setTemplate.safe_substitute(name=set.name, slidegroups='\n'.join(slidegroups)), file=outfile)

for filename in args.presentation:
    ConvertSong(filename)
