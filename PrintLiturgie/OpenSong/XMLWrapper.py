import xml.etree.ElementTree as ET
import collections.abc
from distutils.util import *

class XMLWrapper:

    tagid = ''
    elements = {}

    @classmethod
    def AddElement(cls, element):
        cls.elements[element.tagid] = element

    @staticmethod
    def CreateObject(targettype, xmlnode):
        if hasattr(targettype, 'Create'):
            return targettype.Create(xmlnode)
        else: # Default implementation to create and deserialize an object.
            return targettype().FromXML(xmlnode)

    def __init__(self):
        self.attributes = {}
        self.tags = {}

    def __getattr__(self, name):
        name = name.replace('-', '_')
        if name != 'attributes' and name != 'tags':
            if name in self.attributes:
                return self.attributes[name]
            elif name in self.tags:
                return self.tags[name]

    def __setattr__(self, name, value):
        lname = name.replace('-', '_')
        if lname != 'attributes' and lname != 'tags':
            if lname in self.attributes:
                self.attributes[lname] = value
            elif lname in self.tags:
                self.tags[lname] = value
        object.__setattr__(self, name, value)

    # def __repr__(self):
    #     return '<{0} tagid={1}>'.format(type(self), self.tagid)
    #     pass

    def __dir__(self):
        return [key for key in object.__dir__(self)] + [key for key in self.attributes.keys()] + [key for key in self.tags.keys()]

    def FromXML(self, node):
        for name, value in node.attrib.items():
            name = name.lower() # Noticed OpenSong somtimes mixes case
            if name in self.attributes:
                attrtype = type(self.attributes[name])
                if attrtype == bool:
                    self.attributes[name] = bool(strtobool(value))
                else:
                    self.attributes[name] = type(self.attributes[name])(value)
            else:
                print('*** Unexpected attribute: {0}.{1}'.format(self.tagid, name))

        for child in node:
            tag = child.tag.lower() # Noticed OpenSong somtimes mixes case
            if tag in self.tags:
                tagtype = type(self.tags[tag])
                if tagtype == str:
                    self.tags[tag] = child.text or ''
                else:
                    targettype = self.elements.get(tag)
                    if targettype:
                        newobject = XMLWrapper.CreateObject(targettype, child)
                        if isinstance(self.tags[tag], collections.abc.Container):
                            self.tags[tag].append(newobject)
                        else:
                            self.tags[tag] = newobject
                    else:
                        print('*** Sub-type {1} not defined for {0}'.format(self.tagid, tag))

            else:
                print('*** Unexpected tag: {0}.{1}'.format(self.tagid, tag))

        return self

    def ToXML(self, node = None):
        pass
