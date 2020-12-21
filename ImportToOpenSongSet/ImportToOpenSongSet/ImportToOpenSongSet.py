#! /usr/bin/env python3

# Project imports
from GoogleSheet import GoogleSheet
from DienstenDB import DienstenDB

# System imports
import csv
import appdirs
from datetime import *
import argparse
import xml.etree.ElementTree as ET
import copy
import locale
import os.path

def FindOrCreateElement(target, elementname):
    element = target.find(elementname)
    if element is None:
        element = ET.SubElement(target, elementname)
    return element

class Mededeling:
    def __init__(self, date, body, background = None, disabletitles = None):
        self.date = date
        self.body = body or ''
        self.background = background or ''
        self.disabletitles = bool(disabletitles) # So almost everything other then False or None will disable the titles.

class ImportToOpenSongSet:

    def Process(self, dagen, diensten, mededelingen, presentatie):
        '''Modify an OpenSong set with updated info from the set itself and external spreadsheets
        int dagen:              Standaard aantal dagen voor de start van een mededeling dat deze gebruikt moet worden.
        String[] diensten:      CSV Bestanden met diensten om te laden
        String mededelingen:    CSV Bestand met mededelingen
        String presentatie      XML Bestand met OS pressentatie om aan te passen
        '''
        
        # Determine the working period
        self.activedate = datetime.strptime(os.path.basename(presentatie)[:16], '%Y-%m-%d-%H.%M')
        self.activedate = self.activedate ##- timedelta(days=21)
        self.maxdate = self.activedate + timedelta(days=dagen)

        # Read the presentation
        set = ET.parse(presentatie)
        self.slide_groups = set.find('slide_groups')

        # Do various processing
        self.dienstendb = DienstenDB()
        for file in diensten:
            self.dienstendb.LoadService(file)
        self.dienstendb.CreeerSheets(self.activedate, self.maxdate, 2)
        self.ProcessMededelingen(mededelingen, dagen)
        self.PsalmBord()

        # Write the presentation back. 
        set.write(presentatie, encoding='UTF-8') 

    def AddSlide(slides, bodytext):
        slide = ET.SubElement(slides, 'slide')
        body = ET.SubElement(slide, 'body')
        body.text = bodytext
        return slide

    def PsalmBord(self):
        # Read all songs and scriptures in the presentation.
        songboard = ''
        scriptures = ''
        lastsong = ''
        lastbook = ''
        bundels = {'B38': 'Gezang', 'HH': 'Hemelhoog', 'LvdK': 'Gezang (LvdK)', 'Opw': 'Opwekking', 'DNP': 'Nieuwe Psalmen',
                   'OTH': 'Op Toonhoogte', 'ELB': 'Evang. Liedbundel', 'NLB': 'Nieuw Liedboek'}
        for slide_group in self.slide_groups.iterfind("slide_group"):
            if slide_group.get('type', '') == 'song':
                song = slide_group.get('name')
                if lastsong != song:
                    if songboard:
                        songboard += '\n'
                    nameparts = song.split()
                    nameparts[0] = bundels.get(nameparts[0], nameparts[0])
                    songboard += '♫ ' + ' '.join(nameparts[:2])
                    divider = ' : '
                else:
                    divider = ' / '
                verzen = slide_group.get('presentation')
                verzen = verzen.replace(' C', '')
                verzen = verzen.replace(' V', ', ')
                verzen = verzen.replace('V', '')
                if len(verzen) > 0:
                    songboard += divider + verzen
                lastsong = song
            elif slide_group.get('type', '') == 'scripture':
                scripture = slide_group.get('name')
                if '|' in scripture:
                    scripture = scripture.split('|')[0]
                    book, dummy, verses = scripture.partition(':')
                    if book == lastbook:
                        scriptures += ', ' + verses
                    else:
                        if scriptures:
                            scriptures += '\n'
                        scriptures += scripture
                    lastbook = book
                elif scripture != lastbook:
                    # preformatted
                    if scriptures:
                        scriptures += '\n'
                    scriptures += scripture
                    lastbook = scripture
            else:
                notes = slide_group.find('notes').text
                if notes and notes.find('$lied') >= 0:
                    if songboard:
                        songboard += '\n'
                    songboard += '♫ ' + slide_group.get('name')
            if slide_group.get('name', '') == 'Zegen':  # Do not add anything after this item.
                break
        if len(songboard) == 0:
          songboard = '♫\n' # So we can still replace it lateron.
        else:
            while songboard.find(" 0") >= 0:
                songboard = songboard.replace(" 0", " ")
        # Find all slides that start with a note and replace these with the songboard.
        for body in self.slide_groups.iterfind("./slide_group[@type='custom']/slides/slide/body"):
            if body.text is not None and body.text.startswith('♫'):
                body.text = songboard
                if scriptures:
                    body.text += '\n\n' + scriptures
        
    def DisableTitle(style, title):
        style_title = style.find(title)
        if style_title is None:
            style_title = ET.SubElement(style, title)
        style_title.set('enabled', 'false')

    def ProcessMededelingen(self, mededelingenfiles, dagen):
        # Read the announcements from a csv file.
        mededelingen = []
        custom_mededelingen = []
        dateformat = '%d-%m-%Y'
        for filename in mededelingenfiles:
            with open(filename, newline='') as csvfile:
                for row in csv.reader(csvfile):
                    if row[1] and row[1][:1].isnumeric():
                        todate = datetime.strptime(row[1], dateformat)
                        fromdate = row[0]
                        if fromdate and fromdate[:1].isnumeric:
                            fromdate = datetime.strptime(fromdate, dateformat)
                        else:
                            fromdate = todate - timedelta(days=dagen)
                        if self.activedate >= fromdate and self.activedate <= todate:
                            if row[3]:
                                custom_mededelingen.append(Mededeling(todate, row[2], row[3], row[4]))
                            else:
                                mededelingen.append(Mededeling(todate, row[2]))

        # Remove the old 'extra'(with their own background) announcement groups.
        groups = self.slide_groups.findall('./slide_group[@name="Mededelingen"]') # no delete during iteration.
        for slide_group in groups:
            notes = slide_group.find('notes')
            if notes is not None and notes.text and notes.text.find('$mededelingen_') >= 0:
                self.slide_groups.remove(slide_group)

        # Generate the new announcement slides.
        slideindex = 1
        last_style = None
        for slide_group in self.slide_groups.findall('slide_group'): # don't use an iterator, we modify the collection!
            slidetype = slide_group.get('type', '')
            # Keep tack of the last style. We need it for the 'image' announcements.
            if slidetype == 'style' and slide_group.get('action', '') == 'new':
                style = slide_group.find('style')
                if style:
                    last_style = copy.deepcopy(style)
            # Find the announcement slides.
            if slidetype == 'custom':
                notes = slide_group.find('notes').text
                if notes:

                    # Depricated
                    if notes.find('$bhv') >= 0:
                        subtitle = slide_group.find('subtitle')
                        if subtitle is None:
                            subtitle = ET.SubElement(slide_group, 'subtitle')
                        subtitle.text = self.dienstendb.BHV

                    if notes.find('$dezedienst') >= 0:

                        slides = slide_group.find('slides')
                        slides.clear()                          # Completely rebuild it.
                        ImportToOpenSongSet.AddSlide(slides, self.dienstendb.DezeDienst)
                        subtitle = slide_group.find('subtitle')
                        if subtitle is None:
                            subtitle = ET.SubElement(slide_group, 'subtitle')
                        if self.dienstendb.Bijzonderheid:
                            subtitle.text = self.dienstendb.Bijzonderheid
                        elif self.dienstendb.Kindernevendienst:
                            subtitle.text = self.dienstendb.Kindernevendienst

                    elif notes.find('$collecte') >= 0:
                        slides = slide_group.find('slides')
                        slides.clear()                          # Completely rebuild it.
                        ImportToOpenSongSet.AddSlide(slides, self.dienstendb.Collecte)

                    elif notes.find('$diensten') >= 0:
                        slides = slide_group.find('slides')
                        slides.clear()                          # Completely rebuild it.
                        for sheet in self.dienstendb.KomendeDiensten:
                            ImportToOpenSongSet.AddSlide(slides, sheet)

                    elif notes.find('$mededelingen') >= 0:
                        slide_group.set('loop', 'false')        # Only the last one should loop.
                        slides = slide_group.find('slides')
                        slides.clear()                          # Completely rebuild it.
                        template = copy.deepcopy(slide_group)   # Us the empty original as a template for the others.
                        # Kindernevendienst toevoegen als de subtitle in "deze dienst" al door iets anders gebruikt werd.
                        if self.dienstendb.Bijzonderheid and self.dienstendb.Kindernevendienst:
                            ImportToOpenSongSet.AddSlide(slides, self.dienstendb.Kindernevendienst)
                        # Add the 'simple' ones.
                        for mededeling in mededelingen:
                            ImportToOpenSongSet.AddSlide(slides, mededeling.body)
                        # Add the 'complex' ones with their own background.
                        for mededeling in custom_mededelingen:
                            slide_group = copy.deepcopy(template)
                            self.slide_groups.insert(slideindex, slide_group)
                            slideindex += 1
                            slide_group.find('notes').text = '$mededelingen_extra'
                            slides = slide_group.find('slides')
                            ImportToOpenSongSet.AddSlide(slides, mededeling.body)
                            style = slide_group.find('style')
                            if style is None:
                                if last_style is None:
                                    style = ET.SubElement(slide_group, "style")
                                else:
                                    style = copy.deepcopy(last_style)
                                    slide_group.append(style)
                            style_background = FindOrCreateElement(style, 'background')
                            style_background.set('filename',mededeling.background)
                            style_background.set('position', '2')
                            if mededeling.disabletitles:
                                ImportToOpenSongSet.DisableTitle(style, 'title')
                                ImportToOpenSongSet.DisableTitle(style, 'subtitle')
                        slide_group.set('loop', 'true')         # Make the last slide loop.
            slideindex += 1
                  
# Start as commandline program
if __name__ == "__main__":
    # Command line arguments
    parser = argparse.ArgumentParser(description='Genereer mededelingen in een OpenSong document.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
    Het bestand met mededelingen CSV data moet het volgende fomaat hebben:
        [start datum yyyy-mm-dd],<eind datum yyyy-mm-dd>,<mededeling>,<achtergrond file>
    Het bestand met diensten CSV data moet het volgende fomaat hebben:
        <datum yyyy-mm-ddThh:mm:ss>,<Plaats>,[opmerking],[voorganger],[plaats voorganger],[collecte1],[collecte2]
    Dit kan bijvoorbeeld een standaard CSV export zijn van een spreadsheet programma.
    De achtergrond file zorgt er nu alleen voor dat het item achteraan komt te staan, zodat er
    makkelijk een andere sectie van gemaakt kan worden met die specifieke achtergrond.''')
    parser.add_argument('--dagen', type=int, default=13, help='aantal dagen waarvoor mededelingen meegenomen moeten worden (13)')
    parser.add_argument('-m', '--mededelingen', required=True, metavar='SPREADSHEET', action='append', help='spreadsheet met mededelingen')
    parser.add_argument('-d', '--diensten', required=True, metavar='SPREADSHEET', action='append', help='één of meer spreadsheet met diensten')
    parser.add_argument('-p', '--presentatie', required=True, help='OpenSong presentatie file om aan te passen')
    parser.add_argument('-l', '--locale', help='alternative locale')
    args = parser.parse_args()

    if args.locale:
        locale.setlocale(locale.LC_ALL, args.locale)

    cachedir = appdirs.user_cache_dir(appname='ImportToOpenSongSet', appauthor='OpenSong')
    dienstenfiles = GoogleSheet.ToCSVFiles(cachedir, args.diensten)
    mededelingenfiles = GoogleSheet.ToCSVFiles(cachedir, args.mededelingen)
    ImportToOpenSongSet().Process(args.dagen, dienstenfiles, mededelingenfiles, args.presentatie)
