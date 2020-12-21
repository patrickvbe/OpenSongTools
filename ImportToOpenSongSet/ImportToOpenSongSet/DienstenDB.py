from datetime import *
import csv

class DienstOud:
    ROW_DATUMTIJD = 0
    ROW_PLAATS = 1
    ROW_BIJZONDERHEID = 2
    ROW_VOORGANGER = 3
    ROW_PLAATSVOORGANGER = 4
    ROW_COLLECTE1 = 5
    ROW_COLLECTE2 = 6
    ROW_COLLECTEU = 7
    ROW_KINDERNEVENDIENST = 8
    ROW_BHV = 9
    ROW_ORGANIST = 10

    DT_ISO_FORMAT = '%Y-%m-%dT%H:%M:%S'

    def __init__(self, row):
        self.datum = datetime.strptime(row[self.ROW_DATUMTIJD], self.DT_ISO_FORMAT)
        self.plaats = row[self.ROW_PLAATS]
        self.bijzonderheden = row[self.ROW_BIJZONDERHEID]
        self.predikant = row[self.ROW_VOORGANGER]
        self.predikantplaats = row[self.ROW_PLAATSVOORGANGER]
        self.collecte1 = row[self.ROW_COLLECTE1]
        self.collecte2 = row[self.ROW_COLLECTE2]
        self.collecteu = row[self.ROW_COLLECTEU]
        self.kindernevendienst = row[self.ROW_KINDERNEVENDIENST] if len(row) > self.ROW_KINDERNEVENDIENST else ""
        self.bhv = row[self.ROW_BHV] if len(row) > self.ROW_BHV else ""
        self.organist = row[self.ROW_ORGANIST] if len(row) > self.ROW_ORGANIST else ""

    def __lt__(self, rop):
        return self.datum < rop.datum

class Dienst:
    ROW_DATUMTIJD = 1
    ROW_PLAATS = 2
    ROW_BIJZONDERHEID = 3
    ROW_VOORGANGER = 4
    ROW_PLAATSVOORGANGER = 5
    ROW_BHV = 10
    ROW_ORGANIST = 11
    ROW_KND_JONG = 15
    ROW_KND_OUD = 16
    ROW_COLLECTE1 = 24
    ROW_COLLECTE2 = 25
    ROW_COLLECTEU = 26

    DT_ISO_FORMAT = '%d-%m-%Y %H:%M'

    def __init__(self, row):
        self.datum = datetime.strptime(self.col(row,self.ROW_DATUMTIJD), self.DT_ISO_FORMAT)
        self.plaats = self.col(row, self.ROW_PLAATS)
        self.bijzonderheden = self.col(row, self.ROW_BIJZONDERHEID)
        self.predikant = self.col(row, self.ROW_VOORGANGER)
        self.predikantplaats = self.col(row, self.ROW_PLAATSVOORGANGER)
        self.collecte1 = self.col(row, self.ROW_COLLECTE1)
        self.collecte2 = self.col(row, self.ROW_COLLECTE2)
        self.collecteu = self.col(row, self.ROW_COLLECTEU)
        kndjong = self.col(row, self.ROW_KND_JONG)
        kndoud = self.col(row, self.ROW_KND_OUD)
        self.kindernevendienst = "B" if kndjong and kndoud else "J" if kndjong else ""
        self.bhv = self.col(row, self.ROW_BHV)
        self.organist = self.col(row, self.ROW_ORGANIST)

    def __lt__(self, rop):
        return self.datum < rop.datum

    @staticmethod
    def col(row, col):
        return row[col] if len(row) > col else ""

class DienstenDB:

    def __init__(self):
        self.Diensten = []
        self.kndtekst = { "G" : "Er is vandaag geen\nkindernevendienst",
                          "B" : "Er is voor beide groepen\nkindernevendienst",
                          "J" : "Voor de jongste groep is er\nkindernevendienst"}

    def LoadService(self, filename):
        with open(filename, newline='') as csvfile:
            for row in csv.reader(csvfile):
                dtnieuw = row[Dienst.ROW_DATUMTIJD]
                dtold = row[DienstOud.ROW_DATUMTIJD]
                if dtnieuw and dtnieuw[:1].isnumeric() and dtnieuw.count("-") == 2:
                    self.Diensten.append(Dienst(row))
                elif dtold and dtold[:4].isnumeric():
                    self.Diensten.append(DienstOud(row))

    def FormatPredikant(pretext, predikant, predikantplaats):
        result = ''
        if predikant:
            result += pretext + predikant
        if predikantplaats:
            result += ' uit ' + predikantplaats
        return result

    def FormatDatum(datum, referentie):
        result = ''
        tijd = datum.time()
        if datum.date() == referentie.date():
            if tijd > time(hour=18):
                result = 'Vanavond'
            elif tijd > time(hour=12):
                result = 'Vanmiddag'
            else:
                result = 'Vandaag'
        else:
            result = datum.strftime('%A %d %B')
            result = result[0].upper() + result[1:]
        if tijd != time():
            result += '\nom ' + datum.strftime('%H:%M')
        result = result.replace(" 0", " ")
        return result

    def CreeerSheets(self, vandatum, totdatum, itemspersheet):
        self.DezeDienst = ''
        self.Bijzonderheid = ''
        self.Collecte = ''
        self.KomendeDiensten = []
        self.Kindernevendienst = ''
        self.BHV = ''
        huidigesheet = -1
        items = itemspersheet
        laatstedienst = None    # Soms zijn er dubbele (1 jan)... De eerste wint.
        for dienst in self.Diensten:
            if dienst.datum != laatstedienst and dienst.datum >= vandatum and dienst.datum <= totdatum:
                laatstedienst = dienst.datum
                if dienst.datum == vandatum:
                    self.DezeDienst = dienst.predikant + "\n" + ("uit " + dienst.predikantplaats if dienst.predikantplaats else "") + "\n\n" +\
                                      (dienst.organist if dienst.organist else "") + "\n\n" +\
                                      dienst.bhv
                    self.Bijzonderheid = dienst.bijzonderheden
                    self.Kindernevendienst = self.kndtekst.get(dienst.kindernevendienst, "")

                    if dienst.collecte2:
                        self.Collecte = '1e rondgang: ' + dienst.collecte1 + '\n2e rondgang: ' + dienst.collecte2
                    elif dienst.collecte1:
                        self.Collecte = dienst.collecte1
                    if dienst.collecteu:
                        self.Collecte = self.Collecte + '\nUitgang: ' + dienst.collecteu
                else:
                    items += 1
                    if items > itemspersheet:
                        huidigesheet += 1
                        self.KomendeDiensten.append('')
                        items = 1
                    else:
                        if items > 1:
                            self.KomendeDiensten[huidigesheet] += '\n\n'
                    
                    nieuwesheet = DienstenDB.FormatDatum(dienst.datum, vandatum)
                    if dienst.plaats:
                        nieuwesheet += ' in ' + dienst.plaats
                    nieuwesheet += DienstenDB.FormatPredikant('\n', dienst.predikant, dienst.predikantplaats)
                    if dienst.bijzonderheden:
                        nieuwesheet += '\n' + dienst.bijzonderheden
                    self.KomendeDiensten[huidigesheet] += nieuwesheet
