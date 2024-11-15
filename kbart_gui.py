"""
KBART Filter Tool

Dieses Tool ermöglicht das Filtern von KBART-Dateien basierend auf einer Kaufdatei. 
Fehlende ISBNs werden in einer separaten Datei gespeichert.
"""

import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
import pandas as pd
import numpy as np

def select_file():
    """
    Öffnet einen Dateidialog zur Auswahl einer Datei und gibt den Dateipfad zurück.

    Returns:
        str: Der Dateipfad der ausgewählten Datei oder ein leerer String, 
            wenn keine Datei gewählt wurde.
    """
    return filedialog.askopenfilename()

def save_file(dataframe, message):
    """
    Speichert ein DataFrame in einer Datei und zeigt eine Erfolgsmeldung an.

    Parameters:
        dataframe (pd.DataFrame): Das zu speichernde DataFrame.
        message (str): Die Erfolgsmeldung nach dem Speichern.
    """
    file_path = filedialog.asksaveasfilename(
        defaultextension=".tsv",
        filetypes=[("TSV files", "*.tsv")],
        title="Speichern der neuen KBART-Datei"
    )
    if file_path:
        dataframe.to_csv(file_path, sep='\t', index=False, encoding='utf-8')
        messagebox.showinfo("Gespeichert", f"{message}: {file_path}")

def save_missing_isbns(missing_isbns):
    """
    Speichert eine Liste von fehlenden ISBNs in einer Textdatei.

    Parameters:
        missing_isbns (list): Liste der fehlenden ISBNs.
    """
    if missing_isbns:
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt")],
            title="Speichern der fehlenden ISBNs"
        )
        if file_path:
            # Konvertiere alle Einträge in der Liste in Strings
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write("\n".join(map(str, missing_isbns)))
            messagebox.showinfo("Gespeichert", f"Fehlende ISBNs wurden gespeichert in: {file_path}")

def normalize_isbn(series):
    """
    Normalisiert ISBN-Werte, indem ungültige Einträge entfernt werden.

    Parameters:
        series (pd.Series): Eine Serie mit ISBN-Werten.

    Returns:
        pd.Series: Eine Serie mit normalisierten ISBNs.
    """
    return (
        series.astype(str)
        .str.replace('-', '')
        .str.replace('.0', '', regex=False)
        .str.strip()
        .replace('nan', pd.NA)
        .replace('0', pd.NA)
        .dropna()
    )

def filter_kbart():
    """
    Filtert eine KBART-Datei basierend auf ISBNs aus einer Kaufdatei. 
    Fehlende ISBNs werden gespeichert.
    """
    kbart_file = select_file()
    if not kbart_file:
        messagebox.showwarning("Dateiauswahl", "KBART-Datei nicht ausgewählt.")
        return

    purchase_file = select_file()
    if not purchase_file:
        messagebox.showwarning("Dateiauswahl", "Kaufdatei nicht ausgewählt.")
        return

    isbn_column_number = simpledialog.askinteger(
        "ISBN-Spalte",
        "Bitte Spaltennummer der ISBN in der Kaufdatei angeben (beginnend bei 1):"
    )
    if not isbn_column_number:
        messagebox.showwarning("Eingabe", "Keine ISBN-Spalte angegeben.")
        return

    try:
        # Dateien laden
        kbart_df = pd.read_csv(kbart_file, sep='\t')
        purchase_df = pd.read_excel(purchase_file, skiprows=2)

        # ISBN-Spalte normalisieren
        isbn_column_purchase = purchase_df.columns[isbn_column_number - 1]
        kbart_df['normalized_isbn'] = (
            kbart_df['online_identifier']
            .astype(str)
            .str.replace('-', '')
            .str.replace('.0', '', regex=False)
        )
        purchase_df['normalized_isbn'] = (
            purchase_df[isbn_column_purchase]
            .astype(str)
            .str.replace('-', '')
            .str.replace('.0', '', regex=False)
        )

        # Gefilterte Datensätze
        filtered_kbart_df = kbart_df[
            kbart_df['normalized_isbn'].isin(purchase_df['normalized_isbn'])
        ]

        # Fehlende ISBNs bereinigen
        missing_isbns_series = purchase_df[
            ~purchase_df['normalized_isbn'].isin(kbart_df['normalized_isbn'])
        ]['normalized_isbn']

        # Bereinigung: Entferne NaN, 'nan', '0'
        missing_isbns = (
            missing_isbns_series
            .replace('nan', np.nan)  # 'nan' als NaN behandeln
            .dropna()                # Entfernt echte NaN-Werte
            .astype(str)             # Konvertiert alle Werte in Strings
            .tolist()
        )

        # Entferne explizite "0" Werte
        missing_isbns = [isbn for isbn in missing_isbns if isbn != "0"]

        if missing_isbns:
            save_missing_isbns(missing_isbns)
        else:
            messagebox.showinfo(
                "Ergebnis", 
                "Alle ISBNs aus der Kaufdatei sind in der KBART-Datei vorhanden."
            )

        if not filtered_kbart_df.empty:
            save_file(filtered_kbart_df, "Gefilterte Datei wurde gespeichert als")

    except pd.errors.ParserError as e:
        messagebox.showerror("Fehler", f"Fehler beim Laden der Datei: {e}")
    except KeyError as e:
        messagebox.showerror("Fehler", f"Spalte '{e}' nicht gefunden.")
    except FileNotFoundError as e:
        messagebox.showerror("Fehler", f"Datei nicht gefunden: {e}")
    except ValueError as e:
        messagebox.showerror("Fehler", f"Ungültiger Wert: {e}")
    except Exception as e:  # pylint: disable=broad-exception-caught
        messagebox.showerror("Fehler", f"Ein unbekannter Fehler ist aufgetreten: {e}")

# GUI-Setup
root = tk.Tk()
root.title("KBART Filter Tool")

label = tk.Label(root, text="KBART und Titellisten-Filter", font=("Helvetica", 16))
label.pack(pady=10)

button = tk.Button(root, text="Abgleich starten", command=filter_kbart, font=("Helvetica", 12))
button.pack(pady=10)

info_label = tk.Label(
    root,
    text="Bitte wählen Sie zunächst die KBART-Datei und dann die Titelliste aus.",
    font=("Helvetica", 10)
)
info_label.pack(pady=10)

root.mainloop()
