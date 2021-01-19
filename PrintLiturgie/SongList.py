#! /usr/bin/env python3
from OpenSong.Presentation import *
from OpenSong.Song import *
import argparse
import os.path

def Convert(setfile):
    set = OpenSongSet(setfile)
    try:
        set.Load()
    except Exception as ex:
        print("Failed to load presentation {0}: {1}".format(presentation, str(ex)), file=sys.stderr)
        return
    for slide_group in set.slide_groups:
        slidetype = type(slide_group)
        if slidetype == SlideGroupSong:
            print(slide_group.name, end=': ')
            if slide_group.present:
                for verse in slide_group.present:
                    if verse != 'R':
                        print(verse.replace('V',''), end=' ')
            else:
                print("alle versen ", end='')
            print("=>", os.path.basename(setfile))

# Command line arguments
parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                                 description='Print een liturgie op basis van een OpenSong presentatie.')
parser.add_argument('presentation', nargs='+', help='presentatie files')
args = parser.parse_args()
for filename in args.presentation:
    Convert(filename)
#Convert('/home/patrick/Dropbox/SharedKerkWell/OpenSong/Sets/2021-01-10-10.00-Well')