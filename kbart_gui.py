"""
KBART Filter Tool

Dieses Tool ermöglicht das Filtern von KBART-Dateien basierend auf einer Kaufdatei.
Es werden alle Spalten in der Kaufdatei berücksichtigt, die 'ISBN' im Namen tragen.
ISBNs innerhalb einer Zelle können durch ein Semikolon getrennt sein.
Fehlende ISBNs werden zeilenweise ermittelt und mit der zugehörigen Zeilennummer
gruppiert in einer separaten TSV-Datei gespeichert.
"""

import tkinter as tk
from tkinter import filedialog, messagebox
import pandas as pd

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

# ### GEÄNDERT: Funktion gruppiert die ISBNs pro Zeilennummer vor dem Speichern ###
def save_missing_items(missing_items):
    """
    Gruppiert eine Liste von Tupeln (Zeilennummer, ISBN) nach Zeilennummer
    und speichert das Ergebnis in einer TSV-Datei.

    Parameters:
        missing_items (list): Eine Liste von Tupeln, z.B. [(2, '978...'), (5, '978...')].
    """
    if missing_items:
        file_path = filedialog.asksaveasfilename(
            defaultextension=".tsv",
            filetypes=[("TSV files", "*.tsv"), ("All files", "*.*")],
            title="Speichern der fehlenden ISBNs mit Zeilennummer"
        )
        if file_path:
            # Erstelle ein initiales DataFrame
            initial_df = pd.DataFrame(missing_items, columns=['Zeilennummer_Kaufdatei', 'ISBN'])

            # Gruppiere nach der Zeilennummer und füge die ISBNs mit "; " zusammen
            grouped_df = (
                initial_df
                .groupby('Zeilennummer_Kaufdatei')['ISBN']
                .agg('; '.join)
                .reset_index()
            )

            # Benenne die Spalte um für mehr Klarheit
            grouped_df.rename(columns={'ISBN': 'Nicht_gefundene_ISBNs'}, inplace=True)

            # Speichere das gruppierte DataFrame
            grouped_df.to_csv(file_path, sep='\t', index=False, encoding='utf-8')
            messagebox.showinfo(
                "Gespeichert", f"Fehlende ISBNs wurden gruppiert gespeichert in: {file_path}")

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
        .replace('', pd.NA)
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

    try:
        # Dateien laden
        kbart_df = pd.read_csv(kbart_file, sep='\t')

        if 'publication_type' in kbart_df.columns:
            kbart_df = kbart_df[kbart_df['publication_type'] != 'Serial']

        purchase_df = pd.read_excel(purchase_file)

        # Alle Spalten finden, die "ISBN" im Namen haben
        isbn_columns = [col for col in purchase_df.columns if 'ISBN' in str(col)]
        if not isbn_columns:
            messagebox.showerror(
                "Fehler", "Keine Spalten mit 'ISBN' im Namen in der Kaufdatei gefunden.")
            return

        # Alle ISBNs aus der Kaufdatei für das Filtern sammeln
        all_purchase_isns_raw = []
        for col in isbn_columns:
            cleaned_series = purchase_df[col].dropna().astype(str)
            exploded_series = cleaned_series.str.split(';').explode()
            all_purchase_isns_raw.extend(exploded_series.tolist())

        if not all_purchase_isns_raw:
            messagebox.showinfo("Information", "Keine ISBNs in den gefundenen Spalten gefunden.")
            return

        purchase_isns_series = pd.Series(all_purchase_isns_raw)
        purchase_isbns = normalize_isbn(purchase_isns_series)

        # ISBNs aus der KBART-Datei normalisieren und für schnellen Abgleich in ein Set packen
        online_isbns = normalize_isbn(kbart_df['online_identifier'])
        print_isbns = normalize_isbn(kbart_df['print_identifier'])
        kbart_isbns_set = set(online_isbns.unique()).union(set(print_isbns.unique()))

        # Filtern der KBART-Datei
        filtered_kbart_df = kbart_df[
            normalize_isbn(kbart_df['online_identifier']).isin(purchase_isbns) |
            normalize_isbn(kbart_df['print_identifier']).isin(purchase_isbns)
        ]

        # Fehlende ISBNs mit Zeilennummer erfassen
        missing_items = []
        for index, row in purchase_df.iterrows():
            excel_row_number = index + 2

            isbns_in_row_raw = []
            for col in isbn_columns:
                cell_value = row[col]
                if pd.notna(cell_value):
                    isbns_in_row_raw.extend(str(cell_value).split(';'))

            normalized_isbns_in_row = normalize_isbn(pd.Series(isbns_in_row_raw)).tolist()

            if not normalized_isbns_in_row:
                continue

            match_found_for_row = any(isbn in kbart_isbns_set for isbn in normalized_isbns_in_row)

            if not match_found_for_row:
                for isbn in normalized_isbns_in_row:
                    missing_items.append((excel_row_number, isbn))

        # Speichern und Anzeigen der Ergebnisse
        if missing_items:
            save_missing_items(missing_items)
        else:
            messagebox.showinfo(
                "Ergebnis",
                "Alle Titel aus der Kaufdatei sind in der KBART-Datei vorhanden."
            )

        if not filtered_kbart_df.empty:
            save_file(filtered_kbart_df, "Gefilterte KBART-Datei wurde gespeichert als")
        else:
            messagebox.showinfo(
                "Ergebnis", 
                "Keine Übereinstimmungen gefunden. Die gefilterte KBART-Datei ist leer.")

    except pd.errors.ParserError as e:
        messagebox.showerror(
            "Fehler", 
            f"Fehler beim Laden der Datei: {e}")
    except KeyError as e:
        messagebox.showerror(
            "Fehler", 
            f"Spalte {e} nicht gefunden. Bitte prüfen Sie die Spaltennamen in den Dateien.")
    except FileNotFoundError as e:
        messagebox.showerror(
            "Fehler", f"Datei nicht gefunden: {e}")
    except ValueError as e:
        messagebox.showerror(
            "Fehler", 
            f"Ungültiger Wert: {e}")
    except Exception as e:
        messagebox.showerror(
            "Fehler", 
            f"Ein unerwarteter Fehler ist aufgetreten: {e}")

# GUI-Setup
root = tk.Tk()
root.title("KBART Filter Tool")

label = tk.Label(root, text="KBART und Titellisten-Filter", font=("Helvetica", 16))
label.pack(pady=20)

button = tk.Button(
    root,
    text="Abgleich starten",
    command=filter_kbart,
    font=("Helvetica", 12),
    width=20,
    height=2
)
button.pack(pady=10)

info_label = tk.Label(
    root,
    text="Bitte wählen Sie zuerst die KBART-Datei (.tsv) und dann die Kaufdatei (.xlsx) aus.",
    font=("Helvetica", 10)
)
info_label.pack(pady=10)

root.geometry("400x200")
root.mainloop()
