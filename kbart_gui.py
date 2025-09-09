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
from typing import List, Set, Tuple

import pandas as pd


# --- GUI- und Datei-Hilfsfunktionen ---

def select_file(title: str) -> str:
    """Öffnet einen Dateidialog zur Auswahl einer Datei."""
    return filedialog.askopenfilename(title=title)

def save_dataframe_as_tsv(dataframe: pd.DataFrame, title: str, default_name: str) -> None:
    """Speichert ein DataFrame als TSV-Datei."""
    file_path = filedialog.asksaveasfilename(
        defaultextension=".tsv",
        filetypes=[("TSV files", "*.tsv")],
        title=title,
        initialfile=default_name
    )
    if file_path:
        dataframe.to_csv(file_path, sep='\t', index=False, encoding='utf-8')
        messagebox.showinfo("Gespeichert", f"Datei wurde gespeichert:\n{file_path}")

# --- Datenverarbeitungs-Hilfsfunktionen ---

def normalize_isbns(series: pd.Series) -> pd.Series:
    """Bereinigt eine Serie von ISBNs."""
    return (
        series.astype(str)
        .str.replace('-', '', regex=False)
        .str.replace('.0', '', regex=False)
        .str.strip()
        .replace(['nan', '', '0'], pd.NA)
        .dropna()
    )

def extract_isbns_from_purchase_file(df: pd.DataFrame) -> Tuple[Set[str], List[str]]:
    """Extrahiert alle ISBNs aus den relevanten Spalten der Kaufdatei."""
    isbn_columns = [col for col in df.columns if 'ISBN' in str(col)]
    if not isbn_columns:
        messagebox.showerror(
            "Fehler", "Keine Spalten mit 'ISBN' im Namen in der Kaufdatei gefunden."
        )
        return set(), []

    all_isbns_raw = []
    for col in isbn_columns:
        cleaned_series = df[col].dropna().astype(str)
        exploded_series = cleaned_series.str.split(';').explode()
        all_isbns_raw.extend(exploded_series.tolist())

    purchase_isbns = set(normalize_isbns(pd.Series(all_isbns_raw)))
    return purchase_isbns, isbn_columns

def get_kbart_isbns_as_set(df: pd.DataFrame) -> Set[str]:
    """Extrahiert Online- und Print-ISBNs aus der KBART-Datei und gibt sie als Set zurück."""
    online_isbns = normalize_isbns(df['online_identifier'])
    print_isbns = normalize_isbns(df['print_identifier'])
    return set(online_isbns.unique()).union(set(print_isbns.unique()))

def find_missing_isbns(
    purchase_df: pd.DataFrame, kbart_isbns_set: Set[str], isbn_columns: List[str]
) -> List[Tuple[int, str]]:
    """Findet ISBNs aus der Kaufdatei, die nicht in der KBART-Datei vorhanden sind."""
    missing_items = []
    for index, row in purchase_df.iterrows():
        isbns_in_row_raw = []
        for col in isbn_columns:
            cell_value = row[col]
            if pd.notna(cell_value):
                isbns_in_row_raw.extend(str(cell_value).split(';'))

        normalized_isbns_in_row = normalize_isbns(pd.Series(isbns_in_row_raw)).unique()

        if not any(isbn in kbart_isbns_set for isbn in normalized_isbns_in_row):
            for isbn in normalized_isbns_in_row:
                # +2 für die Excel-Zeilennummer (1-basiert + Header)
                missing_items.append((index + 2, isbn))
    return missing_items

def save_missing_items_grouped(missing_items: List[Tuple[int, str]]) -> None:
    """Gruppiert fehlende ISBNs nach Zeilennummer und speichert sie."""
    if not missing_items:
        messagebox.showinfo(
            "Ergebnis", "Alle Titel aus der Kaufdatei sind in der KBART-Datei vorhanden."
        )
        return

    df = pd.DataFrame(missing_items, columns=['Zeilennummer_Kaufdatei', 'ISBN'])
    grouped_df = (
        df.groupby('Zeilennummer_Kaufdatei')['ISBN']
        .agg('; '.join)
        .reset_index()
        .rename(columns={'ISBN': 'Nicht_gefundene_ISBNs'})
    )
    save_dataframe_as_tsv(grouped_df, "Fehlende ISBNs speichern", "fehlende_ISBNS.tsv")

# --- Hauptlogik ---

def run_filter_process():
    """Orchestriert den gesamten Prozess des Einlesens, Filterns und Speicherns."""
    kbart_file = select_file("Bitte die KBART-Datei (.tsv) auswählen")
    if not kbart_file:
        return

    purchase_file = select_file("Bitte die Kaufdatei (.xlsx) auswählen")
    if not purchase_file:
        return

    try:
        # 1. Daten laden und vorbereiten
        kbart_df = pd.read_csv(kbart_file, sep='\t')
        if 'publication_type' in kbart_df.columns:
            kbart_df = kbart_df[kbart_df['publication_type'] != 'Serial']
        purchase_df = pd.read_excel(purchase_file)

        # 2. ISBNs extrahieren
        purchase_isbns_set, isbn_columns = extract_isbns_from_purchase_file(purchase_df)
        if not isbn_columns:
            return

        kbart_isbns_set = get_kbart_isbns_as_set(kbart_df)

        # 3. KBART-Datei filtern
        filtered_kbart_df = kbart_df[
            normalize_isbns(kbart_df['online_identifier']).isin(purchase_isbns_set) |
            normalize_isbns(kbart_df['print_identifier']).isin(purchase_isbns_set)
        ]

        # 4. Fehlende ISBNs finden und speichern
        missing_items = find_missing_isbns(purchase_df, kbart_isbns_set, isbn_columns)
        save_missing_items_grouped(missing_items)

        # 5. Gefilterte KBART-Datei speichern
        if not filtered_kbart_df.empty:
            save_dataframe_as_tsv(
                filtered_kbart_df, "Gefilterte KBART-Datei speichern", "kbart_gefiltert.tsv"
            )
        else:
            messagebox.showinfo(
                "Ergebnis", "Keine Übereinstimmungen gefunden. Die gefilterte KBART-Datei ist leer."
            )

    except FileNotFoundError as e:
        messagebox.showerror("Fehler", f"Datei nicht gefunden: {e.filename}")
    except (KeyError, ValueError) as e:
        messagebox.showerror("Datenfehler",
                             f"Ein Fehler in den Daten oder Spaltennamen ist aufgetreten: {e}")
    except Exception as e:  # pylint: disable=broad-exception-caught
        # Dies ist ein letztes Sicherheitsnetz für unerwartete Fehler.
        messagebox.showerror(
            "Unerwarteter Fehler",
            f"Ein unerwarteter Fehler ist aufgetreten: {type(e).__name__}\n{e}"
        )

# --- GUI-Setup ---

def main():
    """Initialisiert und startet die Tkinter-Anwendung."""
    root = tk.Tk()
    root.title("KBART Filter Tool")
    root.geometry("400x200")

    tk.Label(root, text="KBART und Titellisten-Filter", font=("Helvetica", 16)).pack(pady=20)

    tk.Button(
        root,
        text="Abgleich starten",
        command=run_filter_process,
        font=("Helvetica", 12),
        width=20,
        height=2
    ).pack(pady=10)

    tk.Label(
        root,
        text="Wählen Sie zuerst die KBART-Datei (.tsv), dann die Kaufdatei (.xlsx).",
        font=("Helvetica", 10)
    ).pack(pady=10)

    root.mainloop()

if __name__ == "__main__":
    main()
