from .XMLWrapper import *

class SongCapo(XMLWrapper):

    tagid = 'capo'

    def __init__(self):
        XMLWrapper.__init__(self)

        # xml attribute members
        self.attributes['print'] = False

class SongBackgrounds(XMLWrapper):

    tagid = 'backgrounds'

    def __init__(self):
        XMLWrapper.__init__(self)

        # xml attribute members
        self.attributes['resize']             = 'screen'
        self.attributes['keep_aspect']        = True
        self.attributes['link']               = True
        self.attributes['background_as_text'] = False

class Song(XMLWrapper):

    tagid = 'song'
    elements = { SongCapo.tagid        : SongCapo,
                 SongBackgrounds.tagid : SongBackgrounds }

    def __init__(self, filename=None):
        XMLWrapper.__init__(self)

        # xml attribute members
        self.tags['title']        = ''
        self.tags['lyrics']       = ''
        self.tags['author']       = ''
        self.tags['copyright']    = ''
        self.tags['hymn_number']  = ''
        self.tags['presentation'] = ''
        self.tags['ccli']         = ''
        self.tags['capo']         = None
        self.tags['key']          = ''
        self.tags['aka']          = ''
        self.tags['key_line']     = ''
        self.tags['user1']        = ''
        self.tags['user2']        = ''
        self.tags['user3']        = ''
        self.tags['theme']        = ''
        self.tags['linked_songs'] = ''
        self.tags['tempo']        = ''
        self.tags['time_sig']     = ''
        self.tags['backgrounds']  = None

        self.filename = filename

    def Save(self):
        pass

    def Load(self):
        if self.filename:
            tree = ET.parse(self.filename)
            root = tree.getroot()
            self.FromXML(root)

    def FromXML(self, node):
        XMLWrapper.FromXML(self, node)
        self.present = self.presentation.upper().split()
        # Split into a dictionary with verses which are lists os sheets (strings)
        self.verses = {}
        currentverse = None
        for line in self.lyrics.splitlines():
            if line.startswith("["):
                currentverse = ['']
                self.verses[line.strip('[] ').upper()] = (currentverse)
            elif line.startswith(" ") and currentverse:
                line = line.strip()
                if line == "||":
                    currentverse.append('')
                else:
                    currentverse[-1] += line + "\n"
        return self

    def ToXML(self):
        self.presentation = " ".join(self.present)
        return XMLWrapper.ToXML(self)
