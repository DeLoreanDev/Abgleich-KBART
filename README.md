# EBS-Abgleich
Das Programm vergleicht KBART- mit Excel-Dateien anhand der ISBN. Mit Beenden des Abgleichs wird eine neue KBART erstellt, welche die Titel aus der Excel-Datei enthält.

Es soll dazu dienen, aus einer großen Anzahl an Titeln in der KBART nur diejenigen auszuwählen, die in der Excel-Tabelle vorhanden sind und sie im KBART-Format bereitzustellen.

Dafür wird die auszuwertende Spalte in der Excel-Datei ausgewählt, in welcher eine ISBN vorkommt.

Sollte eine ISBN nicht in der KBART-, aber in der Excel-Datei vorhanden sein, werden diese als Fehler ausgegeben und können manuell überprüft werden.

Anwendungsbeispiele sind z.B. die Auswahl von EBS-Titeln, Pick&Choose Titeln oder Einzelkäufe von Bibliotheken

Das Programm basiert auf Python und ist auf verschiedenen Systemen wie Windows und Linux ausführbar.
