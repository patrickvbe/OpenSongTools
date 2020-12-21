#! /usr/bin/env python3
from urllib import request
from http import client
import sys
import os.path

class GoogleSheet:
    '''Get csv file from google sheets and cache it or get a cached version of the file or a normal csv file.'''

    def __init__(self, cachedir, document='', documentid='', cachedcsv='', documentname=''):
        ''' Setup the document.
        Args:
            cachedir (str): The directory to put the cached version of the file in.
            document (str): The document url (either http* or a regular file name on disk).
            documentid (str): The google id of the document.
            cachedcsv (str): The full path of the cached file (only used if no document is given).
            documentname (str): An optional real-life name of the file (informational only)
        '''
        self.documentid = documentid        #: str: Google Docs ID string
        self.cachedcsv = cachedcsv          #: str: Full path of the requested file in the cache directory
        self.cachedir = cachedir            #: str: Directory to put a cached version of the file
        self.documentname = documentname    #: str: An optional real-life name for the file
        if document:
            if document.startswith('http'):
                dummy, sep, self.documentid = document.partition("id=")
                self.cachedcsv = os.path.join(cachedir, self.documentid + '.csv')
            elif document.endswith('.csv'):
                self.cachedcsv = document

    def LoadFromGoogle(self):
        ''' Download the file from Google docs. If it fails, it could be that we still have an (old) version
        of the file in the cache which can be used.

        Returns:
            An empty string if successful, an error msg otherwise.
        '''
        if self.documentid == "":
            if self.cachedcsv:
                return ''
            else:
                return 'No document'
        try:
            response = request.urlopen("https://docs.google.com/spreadsheets/d/" + self.documentid + '/export?format=csv')
            if response.getcode() != client.OK:
                return str(response.status + ' / ' + response.reason)
            if response.getheader('Content-Type') != 'text/csv':
                return 'Did not receive csv content'
            else:
                with open(self.cachedcsv, mode='bw') as targetfile:
                    targetfile.write(response.read())
                # See if we got a name for this file...
                content = request.url2pathname(response.getheader('Content-Disposition', '')).split('; ')
                for item in content:
                    name, eq, value = item.partition('=')
                    if name == 'filename*' and len(value) > 7:
                        self.documentname = value[7:]
                return ''
        except Exception as ex:
            return str(ex) 

    def ToCSVFiles(cachedir, filenames):
        ''' Get's a list of files from Google Sheets. Still a bit in development

        Args:
            cachedir (str): The directory for the cached versions of the files.
            filenames (list of str): The documents to get (url or file path).

        Returns:
            list of str: The cached csv files for the given files.
        '''
        resultfiles = []
        for idx, filename in enumerate(filenames):
            doc = GoogleSheet(cachedir, filename)
            result = doc.LoadFromGoogle()
            if result:
                print(filename, 'failed:', result, file=sys.stderr)
            else:
                resultfiles.append(doc.cachedcsv)
        return resultfiles
