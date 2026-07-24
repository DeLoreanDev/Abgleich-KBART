# Abgleich mit KBART Datei
Das Programm vergleicht KBART- mit Excel-Dateien anhand der E-ISBN bzw. Online Identifier. Mit Beenden des Abgleichs wird eine neue KBART erstellt, welche die Titel aus der Excel-Datei enthält.

Es soll dazu dienen, aus einer großen Anzahl an Titeln in der KBART nur diejenigen auszuwählen, die in der Excel-Tabelle vorhanden sind und sie im KBART-Format bereitzustellen.

Dafür wird die auszuwertende Spalte in der Excel-Datei ausgewählt, in welcher eine ISBN vorkommt.

Sollte eine ISBN nicht in der KBART-, aber in der Excel-Datei vorhanden sein, werden diese als Fehler ausgegeben und können manuell überprüft werden.

Anwendungsbeispiele sind z.B. die Auswahl von EBS-Titeln, Pick&Choose Titeln oder Einzelkäufe von Bibliotheken

## Oberfläche

Der gesamte Ablauf findet in einem Fenster statt: beide Dateien auswählen, ISBN-Spalte
bestimmen, Abgleich starten, Ergebnis prüfen, exportieren.

* Die ISBN-Spalte wird über ihren **Namen** gewählt, nicht über eine Spaltennummer.
  Eine Spalte mit "ISBN" im Namen wird automatisch vorgeschlagen, darunter erscheinen
  Beispielwerte zur Kontrolle.
* Vor dem Speichern zeigt das Programm, **was** gefunden wurde: Trefferzahl,
  Anzahl der ISBN ohne Entsprechung, Trefferquote und beide Listen als Tabelle.
* Der Abgleich läuft in einem Hintergrund-Thread, das Fenster bleibt bedienbar.
* Der Filter für Zeitschriften (`publication_type = Serial`) ist als Option sichtbar
  und abschaltbar.
* Helles und dunkles Farbschema.

## Installation

```
pip install -r requirements.txt
python kbart_gui.py
```

Das Programm basiert auf Python und ist auf verschiedenen Systemen wie Windows und Linux ausführbar.
Um es manuell in eine ausführbare Datei umzuwandeln, kann folgender Befehl genutzt werden:

```
pyinstaller --onefile --windowed --hidden-import openpyxl --collect-all customtkinter kbart_gui.py
```

Der Zusatz `--collect-all customtkinter` ist notwendig, weil PyInstaller die
Theme-Dateien des Pakets sonst nicht mit einpackt und die fertige Datei beim Start abbricht.
