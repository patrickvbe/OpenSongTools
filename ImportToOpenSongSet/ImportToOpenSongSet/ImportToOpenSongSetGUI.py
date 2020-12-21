#!/usr/bin/env python3
from GoogleSheet import *
from ImportToOpenSongSet import *
from appdirs import *
from pathlib import Path
from os.path import *
from tkinter.filedialog  import askopenfilename
from configparser import ConfigParser
from tkinter import ttk
import tkinter as tk
import locale

class ConfigEntry(tk.StringVar):
    def __init__(self, configuration, section, entry):
        tk.StringVar.__init__(self)
        self.configuration = configuration
        self.section = section
        self.entry = entry
        self.trace('w', self.vartrace)
    
    def set(self, value):
        if self.configuration[self.section][self.entry] != value:
            self.configuration[self.section][self.entry] = value
            self.configuration.changed = True
        if tk.StringVar.get(self) != value:
            tk.StringVar.set(self, value)

    def get(self):
        return self.configuration[self.section][self.entry]
    
    def vartrace(self, *args):
        self.set(tk.StringVar.get(self))

class Configuration(ConfigParser):

    CFG_SECTION_DATAFILES       = 'datafiles'
    CFG_DIENSTEN_DIT_JAAR       = 'dienstenditjaar'
    CFG_DIENSTEN_VOLGEND_JAAR   = 'dienstenvolgendjaar'
    CFG_MEDEDELINGEN            = 'mededelingen'

    CFG_SECTION_MRU             = 'mru'
    CFG_MRU0                    = 'mru0'

    CFG_SECTION_VARIOUS         = 'various'
    CFG_GEOMETRY                = 'geometry'
    CFG_LOCALE                  = 'locale'
    CFG_DEFAULT_DAYS            = 'default_days'

    def __init__(self):
        ConfigParser.__init__(self, allow_no_value=True)

        # Set the defaults
        self[self.CFG_SECTION_DATAFILES] = {
            self.CFG_DIENSTEN_DIT_JAAR : '',
            self.CFG_DIENSTEN_VOLGEND_JAAR : '',
            self.CFG_MEDEDELINGEN : ''
        }
        self[self.CFG_SECTION_MRU] = {
            self.CFG_MRU0 : ''
        }
        self[self.CFG_SECTION_VARIOUS] = {
            self.CFG_GEOMETRY : '', 
            self.CFG_LOCALE : '',
            self.CFG_DEFAULT_DAYS : '13'
        }
        self.changed = True
        self.appname = 'ImportToOpenSongSet'
        self.appauthor='OpenSong'
        self.cachedir = user_cache_dir(self.appname, self.appauthor)
        os.makedirs(self.cachedir, exist_ok=True)

        # Load from file, if it exists. Otherwise, create.

        self.file = Path(user_config_dir(self.appname, self.appauthor))
        if not self.file.exists():
            self.file.mkdir(parents=True)
        self.file = self.file / 'settings.cfg'
        # Load from old (incorrect) location.
        oldconfigfile = Path(user_data_dir(self.appname, self.appauthor)) / 'settings.cfg'
        if oldconfigfile.is_file():
            oldconfigfile.replace(self.file)
        if self.file.is_file():
            with self.file.open() as file:
                self.read_file(file)
            self.changed = False
        else:
            self.WriteIfChanged()
        # Allow some 'external' control: overide configuration values from a config file in the script folder.
        forcefile = Path(os.path.dirname(__file__)) / 'settings.cfg'
        self.forcefile = str(forcefile)
        if forcefile.is_file():
            with forcefile.open() as file:
                self.read_file(file)
            self.Write()

    def Write(self):
        with self.file.open(mode='w') as file:
            self.write(file)
        self.changed = False

    def WriteIfChanged(self):
        if self.changed:
            self.Write()

class PvBWidget:
    """ Creates a combination of 3 widgets: Label, entry and path selection button.
    These can be used to let the user enter or select a path. The buttons are put
    in the grid layout at the specified row, starting at the startcolumn. Each
    widget is put in a separate column (so +0, +1 and +2).
    """
    def __init__(self, master, label, row=0, startcolumn=0, text=None, configentry=None, pad=3, 
                 entrywidget=None, fileselection=True, textlen=None):
        self.configentry = configentry
        self.label = tk.Label(master, text=label)
        self.label.grid(row=row, column=startcolumn, sticky=tk.W)
        if entrywidget:
            self.entry = entrywidget
        else:
            self.entry = tk.Entry(master)
        if textlen:
            sticky = tk.W
            self.entry.config(width=textlen)
        else:
            sticky = tk.W + tk.E
        self.entry.grid(row=row, column=startcolumn+1, pady=pad, sticky=sticky)
        if configentry:
            self.entry.config(textvariable=configentry)
            text = configentry.get()
        if text:
            self.entry.insert(0, text)
        self.entry.xview_moveto(1.0)
        if fileselection:
            self.select = tk.Button(master, text='...', command=self.SelectFile)
            self.select.grid(row=row, column=startcolumn+2, padx=(0, pad), pady=pad)

    def SelectFile(self):
        name= askopenfilename(initialfile=self.entry.get(), title=self.label.cget('text'))
        if name:
            self.entry.delete(0, tk.END)
            self.entry.insert(0,name)
            self.entry.xview_moveto(1.0)  

class Application(tk.Frame):
    
    padsize = 3

    def __init__(self, master=None):
        tk.Frame.__init__(self, master)

        self.configuration = Configuration()
        self.cfg_geometry = ConfigEntry(self.configuration, Configuration.CFG_SECTION_VARIOUS, Configuration.CFG_GEOMETRY)
        self.pack(fill=tk.BOTH, expand=tk.YES)
        self.actions = ActionsFrame(self)
        self.actions.pack(side=tk.TOP, fill=tk.BOTH, expand=tk.YES)
        # ttk.Separator(self, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)
        self.config = ConfigurationFrame(self)
        self.config.pack(side=tk.TOP, fill=tk.X, expand=tk.NO, padx=self.padsize, pady=self.padsize)
        root.geometry(self.cfg_geometry.get())
        root.protocol("WM_DELETE_WINDOW", self.OnClose)

    def OnClose(self):
        self.cfg_geometry.set(root.geometry())
        root.destroy()

class ActionsFrame(tk.Frame):
    def __init__(self, master=None):
        tk.Frame.__init__(self, master)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(2, weight=1)
        self.folder = ''

        # The main controls for 'daily' use
        self.entry = ttk.Combobox(self)
        configuration = master.configuration
        self.configentry = ConfigEntry(configuration, Configuration.CFG_SECTION_MRU, Configuration.CFG_MRU0)
        self.configentry.trace('w', self.EntryChanged)
        PvBWidget(self, "OpenSong set", entrywidget=self.entry, configentry=self.configentry )
        self.nodownload = tk.IntVar(0)
        checkbox = tk.Checkbutton(self, text="Niets downloaden!", variable=self.nodownload)
        checkbox.grid(row=1, column=0)
        self.btn_generate = tk.Button(self, text='Genereer', command=self.Genereer)
        self.btn_generate.grid(row=1, column=1, columnspan=2)

        # Add a log area to the GUI        
        frame = tk.Frame(self)
        frame.grid(row=2, column=0, columnspan=3, padx=master.padsize, pady=master.padsize, sticky=tk.NSEW)
        self.txt_output = tk.Text(frame, wrap=tk.WORD, state=tk.DISABLED, height=4)
        self.txt_output.pack(side=tk.LEFT, fill=tk.BOTH, expand=tk.YES)
        self.txt_output.tag_config("error", foreground="red")
        scrollbar = tk.Scrollbar(frame)
        scrollbar.pack(side=tk.LEFT, fill=tk.Y)
        scrollbar.config(command=self.txt_output.yview)
        self.txt_output.config(yscrollcommand=scrollbar.set)
        self.Log('forcefile: ' + configuration.forcefile)

    def EntryChanged(self, *args):
        dirname = os.path.dirname(tk.StringVar.get(self.configentry))
        if dirname != self.folder:
            self.folder = dirname
            entries = []
            path = Path(dirname)
            entrynr = 0
            if path.is_dir():
                for direntry in path.iterdir():
                    if direntry.is_file():
                        entries.append(str(direntry))
            self.entry.configure(values=sorted(entries))
            #             entries[str(direntry.stat().st_mtime) + str(entrynr)] = str(direntry)
            #             entrynr += 1
            # self.entry.configure(values=[entries[i] for i in reversed(sorted(entries))])

    def FlushLog(self):
        self.txt_output.configure(state=tk.NORMAL)
        self.txt_output.delete(1.0, tk.END)
        self.txt_output.configure(state=tk.DISABLED)

    def Log(self, text, error=False):
        self.txt_output.configure(state=tk.NORMAL)
        tags = ()
        if error:
            tags = ("error")
        self.txt_output.insert(tk.END, text.encode('cp1252','replace').decode('cp1252') + '\n', tags)
        self.txt_output.configure(state=tk.DISABLED)
        self.txt_output.see(tk.END)
        self.txt_output.update_idletasks()

    def GetFile(self, configuration, section, entry, nodownload):
        filespecifier = configuration.get(section, entry)
        if filespecifier:
            self.Log('Laden van ' + filespecifier)
            gs = GoogleSheet(configuration.cachedir, filespecifier)
            if nodownload:
                errormsg = 'Bestand wordt niet gedownload'
            else:
                errormsg = gs.LoadFromGoogle()
            if errormsg:
                self.Log(errormsg, error=True)
                if gs.cachedcsv and os.path.isfile(gs.cachedcsv):
                    self.Log('Gebruik het bestand uit de cache: ' + gs.cachedcsv)
                    return gs.cachedcsv
                self.Log('Geen bestand aanwezig in de cache', error=True)
            else:
                if gs.documentname:
                    self.Log('Ontvangen: ' + gs.documentname)
                return gs.cachedcsv

    def Genereer(self):
        conf = app.configuration
        diensten = []
        mededelingen = []
        self.FlushLog()
        self.Log('Genereren...')
        try:
            dagen = 13
            var = conf.get(conf.CFG_SECTION_VARIOUS, conf.CFG_DEFAULT_DAYS)
            if var:
               dagen = int(var) 
            var = conf.get(conf.CFG_SECTION_VARIOUS, conf.CFG_LOCALE)
            if var:
                locale.setlocale(locale.LC_ALL, var)
            nodownload = self.nodownload.get()
            var = self.GetFile(conf, conf.CFG_SECTION_DATAFILES, conf.CFG_DIENSTEN_DIT_JAAR, nodownload)
            if var:
                diensten.append(var)
            var = self.GetFile(conf, conf.CFG_SECTION_DATAFILES, conf.CFG_DIENSTEN_VOLGEND_JAAR, nodownload)
            if var:
                diensten.append(var)
            var = self.GetFile(conf, conf.CFG_SECTION_DATAFILES, conf.CFG_MEDEDELINGEN, nodownload)
            if var:
                mededelingen.append(var)
            osset = conf.get(conf.CFG_SECTION_MRU, conf.CFG_MRU0)
            self.Log('Verwerken van ' + osset)
            ImportToOpenSongSet().Process(dagen, diensten, mededelingen, osset )
        except Exception as ex:
            self.Log('Fout: ' + str(ex), error=True)
        else:
            self.Log('Klaar.')


class ConfigurationFrame(tk.LabelFrame):
    def __init__(self, master=None):
        tk.LabelFrame.__init__(self, master, text='Instellingen')
        self.columnconfigure(1, weight=1)
        gridrow = 0
        widget_entries = [ ('Diensten sheet dit jaar',      Configuration.CFG_DIENSTEN_DIT_JAAR),
                           ('Diensten sheet volgend jaar',  Configuration.CFG_DIENSTEN_VOLGEND_JAAR),
                           ('Mededelingen sheet',           Configuration.CFG_MEDEDELINGEN) ]
        for label, configname in widget_entries:
            PvBWidget(self, label, gridrow, configentry=ConfigEntry(master.configuration, Configuration.CFG_SECTION_DATAFILES, configname))
            gridrow += 1
        widget_entries = [ ('Mededelingen periode (dagen)', Configuration.CFG_DEFAULT_DAYS),
                           ('Afwijkende locale',            Configuration.CFG_LOCALE) ]
        for label, configname in widget_entries:
            PvBWidget(self, label, gridrow, configentry=ConfigEntry(master.configuration, Configuration.CFG_SECTION_VARIOUS, configname),
                        fileselection=False, textlen=15)
            gridrow += 1


root = tk.Tk()
app = Application()
app.master.title('OpenSong sets aanvullen vanuit (google) csv files (2020.12.17)')
app.mainloop()             
app.configuration.WriteIfChanged()
