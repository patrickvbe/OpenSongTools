# OpenSong tools

## General

These are some tool we use internally in hour church to assist around using OpenSong.

## ImportOpenSongSet

Adds stuff to an OpenSong set:
* Adds a song / reading overview
* Adds information about the current and upcoming services, based on the content of one or two (the next year) Google Sheet documents.
* Adds announcements, based on a Google Sheet document. 

## PrintLiturgie

Transforms the set to a different (textual) format. The default is HTML, but with the command line arguments, you can modify this to anything you like. The output format includes the complete text of the selected songs. So you can use the output as an input for documents or web sites.

## Various OneFileTools

This is a collection of some small tools that consist of only one file:
* WatchToLilyPond.py : Watches a certain file location (e.g. the default location you write your MuseScore files) for new / changed files. Note: additional packages to install are mentioned in the comment block at the start of the file. If found, it converts the files like this (with tools you have to install separate):
  * .mscz files (MuseScore) are converted with musescore to MusicXML files
  * .xml (MusicXML) files are converted to LilyPond files with musicxml2ly
  * .ly (LilyPond) files are used to extract the bare notes from. Thes are then 'cleaned' and either printed out or put on the clipboard, ready to paste into OpenSong to be rendered.
  * Note that each step will automatically trigger the next, because the files are written in the same folder. So e.g. a written .mscz file will directly end-up on your clipboard as paste-able notes...
* WrapSongs.py : Re-wraps the song text in an OpenSong song file according to rules you specify so they better fit on the slides. Optionally adds verse information.

