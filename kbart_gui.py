"""
KBART Filter Tool

This script creates a GUI application for filtering a KBART file 
based on the ISBNs present in a purchase file.
"""
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
import pandas as pd

def select_file():
    """
    Open a file dialog to select a file and return the selected file's path.

    Parameters:
    None. The function does not take any parameters.

    Returns:
    str: The file path of the selected file. If no file is selected, an empty string is returned.
    """
    file_path = filedialog.askopenfilename()
    return file_path

def save_file(dataframe):
    """
    Save a pandas DataFrame to a file using a file dialog for selecting the save location.

    Parameters:
    dataframe (pandas.DataFrame): The DataFrame to be saved.

    Returns:
    None. The function saves the DataFrame to a file and displays a message with the save status.
    """
    file_path = filedialog.asksaveasfilename(
        defaultextension=".tsv",
        filetypes=[("TSV files", "*.tsv")])
    if file_path:
        dataframe.to_csv(file_path, sep='\t', index=False)
        messagebox.showinfo("Gespeichert", f"Gefilterte Datei wurde gespeichert als: {file_path}")

def filter_kbart():
    """
    This function filters a KBART file based on the ISBNs present in a purchase file.
    It loads the KBART and purchase files, normalizes the ISBNs, and checks for matches.
    It also displays missing ISBNs and allows the user to save the filtered KBART data.

    Parameters:
    None. The function does not take any parameters.

    Returns:
    None. The function performs the filtering, displays messages, and saves the filtered data.
    """
    # KBART-Datei auswählen
    kbart_file = select_file()
    if not kbart_file:
        messagebox.showwarning("Dateiauswahl", "KBART-Datei nicht ausgewählt.")
        return

    # Kaufdatei auswählen
    purchase_file = select_file()
    if not purchase_file:
        messagebox.showwarning("Dateiauswahl", "Kaufdatei nicht ausgewählt.")
        return

    # Spaltennummer für ISBN eingeben (beginnend bei 1)
    isbn_column_number = simpledialog.askinteger(
        "ISBN-Spalte", 
        "Bitte Spaltennummer der ISBN in der Kaufdatei angeben (beginnend bei 1):")
    if not isbn_column_number:
        messagebox.showwarning("Eingabe", "Keine ISBN-Spalte angegeben.")
        return

    try:
        # Dateien laden
        kbart_df = pd.read_csv(kbart_file, sep='\t')
        purchase_df = pd.read_excel(purchase_file, skiprows=2)

        # Überprüfen, ob die Spaltennummer gültig ist
        if isbn_column_number < 1 or isbn_column_number > len(purchase_df.columns):
            messagebox.showerror("Fehler", "Ungültige Spaltennummer für die Kaufdatei.")
            return

        # Spalte anhand der Nummer auswählen und ISBNs normalisieren
        # (Bindestriche entfernen und als String formatieren)

        # Umwandlung zur Spaltennummer
        isbn_column_purchase = purchase_df.columns[isbn_column_number - 1]
        # Spalte 'online_identifier' als String formatieren
        online_identifier_series = kbart_df['online_identifier'].astype(str)

        # Bindestriche und '.0' entfernen
        normalized_isbn = (
            online_identifier_series
            .str.replace('-', '')
            .str.replace('.0', '', regex=False)
        )

        # Ergebnis der neuen Spalte zuweisen
        kbart_df['normalized_isbn'] = normalized_isbn
        # Spalte als String formatieren
        isbn_series = purchase_df[isbn_column_purchase].astype(str)

        # Bindestriche und '.0' entfernen
        isbn_normalized = (
            isbn_series
            .str.replace('-', '')
            .str.replace('.0', '', regex=False)
        )
        # Ergebnis der neuen Spalte zuweisen
        purchase_df['normalized_isbn'] = isbn_normalized

        # Gefilterte KBART-Datensätze basierend auf vorhandenen ISBNs in der Kaufdatei
        filtered_kbart_df = kbart_df[
            kbart_df['normalized_isbn'].isin(purchase_df['normalized_isbn'])
        ]

        # Fehlende ISBNs aus der Kaufdatei, die nicht in der KBART-Datei vorhanden sind
        missing_isbns_series = purchase_df[
            ~purchase_df['normalized_isbn'].isin(kbart_df['normalized_isbn'])
        ]['normalized_isbn']

        # Fehlende ISBNs als Liste umwandeln
        missing_isbns = missing_isbns_series.tolist()

        # Ergebnis anzeigen
        if missing_isbns:
            messagebox.showinfo(
                "Fehlende ISBNs", 
                f"ISBNs die nicht in der KBART-Datei vorkommen:\n{', '.join(missing_isbns)}")
        else:
            messagebox.showinfo(
                "Ergebnis", 
                "Alle ISBNs aus der Kaufdatei sind in der KBART-Datei vorhanden.")

        # Gefilterte Datensätze speichern
        if not filtered_kbart_df.empty:
            save_file(filtered_kbart_df)

    except pd.errors.ParserError as e:
        messagebox.showerror("Fehler", f"Fehler beim Laden der Datei: {e}")
    except KeyError as e:
        messagebox.showerror("Fehler", f"Spalte '{e}' nicht gefunden.")
    except FileNotFoundError as e:
        messagebox.showerror("Fehler", f"Datei nicht gefunden: {e}")
    except ValueError as e:
        messagebox.showerror("Fehler", f"Ungültiger Wert: {e}")
    except Exception as e: # pylint: disable=broad-exception-caught
        messagebox.showerror("Fehler", f"Ein unbekannter Fehler ist aufgetreten: {e}")


# GUI-Fenster erstellen
root = tk.Tk()
root.title("KBART Filter Tool")

label = tk.Label(
    root,
    text="KBART und Titellisten-Filter",
    font=("Helvetica", 16))
label.pack(pady=10)

button = tk.Button(
    root, text="Abgleich starten",
    command=filter_kbart,
    font=("Helvetica", 12))
button.pack(pady=10)

info_label = tk.Label(
    root,
    text="Bitte wählen Sie zunächst die KBART-Datei und dann die Titelliste aus.",
    font=("Helvetica", 10))
info_label.pack(pady=10)

root.mainloop()
