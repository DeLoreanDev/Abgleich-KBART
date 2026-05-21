"""
KBART Filter Tool

Dieses Tool ermöglicht das Filtern von KBART-Dateien basierend auf einer Kaufdatei.
Fehlende ISBNs werden in einer separaten Datei gespeichert.
"""

import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
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
            try:
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write("\n".join(map(str, missing_isbns)))
                messagebox.showinfo(
                    "Gespeichert",
                    f"Fehlende ISBNs wurden gespeichert in: {file_path}"
                )
            except OSError as e:
                messagebox.showerror("Fehler", f"Fehler beim Schreiben der Datei: {e}")


def normalize_isbn(series):
    """
    Normalisiert ISBN-Werte, indem Formatierungsartefakte entfernt werden.
    Ungültige Werte ('nan', '0') werden durch pd.NA ersetzt.
    Die zurückgegebene Series hat dieselbe Länge wie die Eingabe.

    Parameters:
        series (pd.Series): Eine Serie mit ISBN-Werten.

    Returns:
        pd.Series: Eine Serie mit normalisierten ISBNs (gleiche Länge wie Eingabe).
    """
    return (
        series.astype(str)
        .str.replace('-', '', regex=False)
        .str.replace('.0', '', regex=False)
        .str.strip()
        .replace('nan', pd.NA)
        .replace('0', pd.NA)
    )


def _collect_inputs():
    """
    Fordert den Nutzer zur Auswahl von KBART-Datei, Kaufdatei und ISBN-Spalte auf.

    Returns:
        tuple: (kbart_file, purchase_file, isbn_column_number) oder None bei Abbruch.
    """
    kbart_file = select_file()
    if not kbart_file:
        messagebox.showwarning("Dateiauswahl", "KBART-Datei nicht ausgewählt.")
        return None

    purchase_file = select_file()
    if not purchase_file:
        messagebox.showwarning("Dateiauswahl", "Kaufdatei nicht ausgewählt.")
        return None

    isbn_column_number = simpledialog.askinteger(
        "ISBN-Spalte",
        "Bitte Spaltennummer der ISBN in der Kaufdatei angeben (beginnend bei 1):"
    )
    if isbn_column_number is None or isbn_column_number <= 0:
        messagebox.showwarning("Eingabe", "Keine gültige ISBN-Spalte angegeben.")
        return None

    return kbart_file, purchase_file, isbn_column_number


def filter_kbart():
    """
    Filtert eine KBART-Datei basierend auf ISBNs aus einer Kaufdatei.
    Fehlende ISBNs werden gespeichert.
    """
    inputs = _collect_inputs()
    if not inputs:
        return

    kbart_file, purchase_file, isbn_column_number = inputs

    try:
        kbart_df = pd.read_csv(kbart_file, sep='\t', encoding='utf-8-sig')

        if 'publication_type' in kbart_df.columns:
            kbart_df = kbart_df[kbart_df['publication_type'] != 'Serial']

        purchase_df = pd.read_excel(purchase_file)

        if isbn_column_number > len(purchase_df.columns):
            messagebox.showwarning(
                "Eingabe",
                f"Die Kaufdatei hat nur {len(purchase_df.columns)} Spalten."
            )
            return

        # ISBN-Spalte aus der Kaufdatei normalisieren (nur gültige Werte behalten)
        isbn_column_purchase = purchase_df.columns[isbn_column_number - 1]
        purchase_isbns = normalize_isbn(purchase_df[isbn_column_purchase]).dropna()

        # ISBNs aus der KBART-Datei normalisieren — gleiche Länge wie kbart_df
        # beibehalten für korrektes Boolean-Masking (NaN in .isin() wird als False behandelt)
        online_isbns = normalize_isbn(kbart_df['online_identifier'])
        print_isbns = normalize_isbn(kbart_df['print_identifier'])

        # Kombinierter Satz von KBART-ISBNs (NaN explizit ausschließen)
        kbart_isbns_set = set(online_isbns.dropna()) | set(print_isbns.dropna())

        # Filtern der KBART-Datei — vorberechnete Series wiederverwenden
        filtered_kbart_df = kbart_df[
            online_isbns.isin(purchase_isbns) |
            print_isbns.isin(purchase_isbns)
        ]

        # Fehlende ISBNs finden (purchase_isbns ist bereits bereinigt)
        missing_isbns = purchase_isbns[
            ~purchase_isbns.isin(kbart_isbns_set)
        ].tolist()

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
    except IndexError as e:
        messagebox.showerror("Fehler", f"Spaltenindex außerhalb des gültigen Bereichs: {e}")
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
