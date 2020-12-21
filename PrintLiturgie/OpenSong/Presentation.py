from .XMLWrapper import *

class Tab(XMLWrapper):

    tagid = 'tab'

    ALIGN_LEFT    = 'left'
    ALIGN_CENTER  = 'center'
    ALIGN_RIGH    = 'right'

    def __init__(self):
        XMLWrapper.__init__(self)
        # xml attribute members
        self.attributes['align']    = Tab.ALIGN_LEFT
        self.attributes['position'] = 0

class Tabs(XMLWrapper):

    tagid = 'tabs'
    elements = { Tab.tagid : Tab }

    @staticmethod
    def Create(xmlnode):
        result = Tabs().FromXML(xmlnode)
        return result.tab

    def __init__(self):
        XMLWrapper.__init__(self)
        # xml tag members
        self.tags['tab'] = []

class BaseStyle(XMLWrapper):

    ALIGN_LEFT    = 'left'
    ALIGN_CENTER  = 'center'
    ALIGN_RIGH    = 'right'
    VALIGN_TOP    = 'top'
    VALIGN_CENTER = 'center'
    VALIGN_BOTTOM = 'bottom'

    def __init__(self):
        XMLWrapper.__init__(self)

        # xml attribute members
        self.attributes['align']         = BaseStyle.ALIGN_CENTER
        self.attributes['valign']        = BaseStyle.VALIGN_CENTER
        self.attributes['bold']          = False
        self.attributes['border']        = False
        self.attributes['border_color']  = ''
        self.attributes['color']         = ''
        self.attributes['enabled']       = ''
        self.attributes['fill']          = False
        self.attributes['fill_color']    = ''
        self.attributes['font']          = ''
        self.attributes['size']          = 12
        self.attributes['underline']     = False
        self.attributes['italic']        = False
        self.attributes['margin-bottom'] = 0
        self.attributes['margin-left']   = 0
        self.attributes['margin-right']  = 0
        self.attributes['margin-top']    = 0
        self.attributes['shadow']        = False
        self.attributes['shadow_color']  = ''

class TitleStyle(BaseStyle):

    tagid = 'title'

    def __init__(self):
        BaseStyle.__init__(self)

        # xml attribute members
        self.attributes['include_verse'] = False

class SubtitleStyle(BaseStyle):

    tagid = 'subtitle'

    def __init__(self):
        BaseStyle.__init__(self)

        # xml attribute members
        self.attributes['descriptive'] = False

class BodyStyle(BaseStyle):

    tagid = 'body'
    elements = { Tabs.tagid : Tabs}
    elements.update(BaseStyle.elements)

    def __init__(self):
        BaseStyle.__init__(self)

        # xml attribute members
        self.attributes['auto_scale']          = False
        self.attributes['highlight_chorus']    = False
        self.attributes['multilanguage_color'] = '#DCDCDC'
        self.attributes['multilanguage_size']  = 70

        # xml tag members
        self.tags['tabs'] = None

class BackgroundStyle(XMLWrapper):

    tagid = 'background'

    def __init__(self):
        XMLWrapper.__init__(self)

        # xml attribute members
        self.attributes['color']        = '#000000'
        self.attributes['position']     = 1
        self.attributes['strip_footer'] = 0
    
class StyleDefinition(XMLWrapper):
    tagid = 'style'
    elements = { TitleStyle.tagid : TitleStyle,
                 SubtitleStyle.tagid : SubtitleStyle,
                 BodyStyle.tagid : BodyStyle,
                 BackgroundStyle.tagid : BackgroundStyle }

    def __init__(self):
        XMLWrapper.__init__(self)

        # xml attribute members
        self.attributes['index'] = ''

        # xml tag members
        self.tags['title']         = None
        self.tags['subtitle']      = None
        self.tags['body']          = None
        self.tags['background']    = None
        self.tags['song_subtitle'] = ''

class Slide(XMLWrapper):
    
    tagid = 'slide'

    def __init__(self):
        XMLWrapper.__init__(self)
        # xml tag members
        self.tags['body'] = ''

class Slides(XMLWrapper):

    tagid = 'slides'
    elements = { Slide.tagid : Slide }

    @staticmethod
    def Create(xmlnode):
        result = Slides().FromXML(xmlnode)
        return result.slide

    def __init__(self):
        XMLWrapper.__init__(self)
        # xml tag members
        self.tags['slide'] = []

class SlideGroup(XMLWrapper):

    tagid = 'slide_group'
    elements = { StyleDefinition.tagid : StyleDefinition }
    slide_groups = {}

    @staticmethod
    def Create(xmlnode):
        subtype = xmlnode.attrib.get('type')
        subclass = SlideGroup.slide_groups.get(subtype)
        if subclass:
            return subclass().FromXML(xmlnode)
        else:
            print("*** Subclass for slide_group type {0} not found:".format(subtype))

    def __init__(self):
        XMLWrapper.__init__(self)

        # xml attribute members
        self.attributes['name']       = ''
        self.attributes['transition'] = 0

        # sub items
        self.tags['style'] = None
        self.tags['presentation'] = ''

class SlideGroups(XMLWrapper):

    tagid = 'slide_groups'
    elements = { SlideGroup.tagid : SlideGroup }

    @staticmethod
    def Create(xmlnode):
        result = SlideGroups().FromXML(xmlnode)
        return result.slide_group

    def __init__(self):
        XMLWrapper.__init__(self)
        # xml tag members
        self.tags['slide_group'] = []

class SlideGroupCustom(SlideGroup):

    elements = { Slides.tagid : Slides }
    elements.update(SlideGroup.elements)

    def __init__(self):
        SlideGroup.__init__(self)
        self.attributes['type'] = 'custom'

        # xml attribute members
        self.attributes['loop']    = False
        self.attributes['seconds'] = 0
        self.attributes['print']   = True

        # xml tag members
        self.tags['title']    = ''
        self.tags['subtitle'] = ''
        self.tags['notes']    = ''
        self.tags['slides']   = None

SlideGroup.slide_groups['custom'] = SlideGroupCustom

class SlideGroupScripture(SlideGroup):

    elements = { Slides.tagid : Slides }
    elements.update(SlideGroup.elements)

    def __init__(self):
        SlideGroup.__init__(self)
        self.attributes['type'] = 'scripture'

        # xml attribute members
        self.attributes['loop']    = False
        self.attributes['seconds'] = 0
        self.attributes['print']   = True

        # xml tag members
        self.tags['title']    = ''
        self.tags['subtitle'] = ''
        self.tags['notes']    = ''
        self.tags['slides']   = None

SlideGroup.slide_groups['scripture'] = SlideGroupScripture

class SlideGroupSong(SlideGroup):

    def __init__(self):
        SlideGroup.__init__(self)
        self.attributes['type'] = 'song'

        # xml attribute members
        self.attributes['presentation'] = ''
        self.attributes['path']         = ''

        # other attributes
        self.verses = []    # This one is leading over presentation

    def FromXML(self, node):
        SlideGroup.FromXML(self, node)
        self.present = self.presentation.upper().split()
        return self

    def ToXML(self):
        self.presentation = " ".join(self.present)
        return SlideGroup.ToXML(self)

SlideGroup.slide_groups['song'] = SlideGroupSong

class OpenSongSet(XMLWrapper):

    tagid = 'set'
    elements = { SlideGroups.tagid : SlideGroups }

    def __init__(self, filename=None):
        XMLWrapper.__init__(self)

        self.filename = filename

        # xml attribute members
        self.attributes['name'] = ''

        # xml tag members
        self.tags['slide_groups'] = None

    def Save(self):
        pass

    def Load(self):
        if self.filename:
            tree = ET.parse(self.filename)
            root = tree.getroot()
            self.FromXML(root)
