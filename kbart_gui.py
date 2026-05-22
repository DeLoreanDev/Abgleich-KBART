# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024 DeLoreanDev
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

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
        try:
            dataframe.to_csv(file_path, sep='\t', index=False, encoding='utf-8')
            messagebox.showinfo("Gespeichert", f"Datei wurde gespeichert:\n{file_path}")
        except OSError as e:
            messagebox.showerror("Fehler", f"Fehler beim Schreiben der Datei: {e}")


# --- Datenverarbeitungs-Hilfsfunktionen ---

def normalize_isbns(series: pd.Series) -> pd.Series:
    """
    Bereinigt eine Serie von ISBNs.
    Gibt eine Series gleicher Länge zurück (kein dropna), damit sie sicher
    als Boolean-Maske auf DataFrames angewendet werden kann.
    NaN-Werte in .isin() werden automatisch als False behandelt.
    """
    return (
        series.astype(str)
        .str.replace('-', '', regex=False)
        .str.replace('.0', '', regex=False)
        .str.strip()
        .replace(['nan', '', '0'], pd.NA)
    )


def extract_isbns_from_purchase_file(df: pd.DataFrame) -> Tuple[Set[str], List[str]]:
    """Extrahiert alle ISBNs aus Spalten, die 'ISBN' im Namen tragen."""
    isbn_columns = [col for col in df.columns if 'ISBN' in str(col)]
    if not isbn_columns:
        messagebox.showerror(
            "Fehler", "Keine Spalten mit 'ISBN' im Namen in der Kaufdatei gefunden."
        )
        return set(), []

    all_isbns_raw = []
    for col in isbn_columns:
        exploded = df[col].dropna().astype(str).str.split(';').explode()
        all_isbns_raw.extend(exploded.tolist())

    purchase_isbns = set(normalize_isbns(pd.Series(all_isbns_raw)).dropna())
    return purchase_isbns, isbn_columns


def get_kbart_isbns_as_set(df: pd.DataFrame) -> Set[str]:
    """Extrahiert Online- und Print-ISBNs aus der KBART-Datei als Set."""
    online = normalize_isbns(df['online_identifier']).dropna()
    print_ = normalize_isbns(df['print_identifier']).dropna()
    return set(online) | set(print_)


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

        normalized = normalize_isbns(pd.Series(isbns_in_row_raw)).dropna().unique()

        if not any(isbn in kbart_isbns_set for isbn in normalized):
            for isbn in normalized:
                missing_items.append((index + 2, isbn))  # +2: 1-basiert + Header
    return missing_items


def save_missing_items_grouped(missing_items: List[Tuple[int, str]]) -> None:
    """Gruppiert fehlende ISBNs nach Zeilennummer und speichert sie als TSV."""
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
    save_dataframe_as_tsv(grouped_df, "Fehlende ISBNs speichern", "fehlende_ISBNs.tsv")


# --- Hauptlogik ---

def run_filter_process() -> None:
    """Orchestriert den gesamten Prozess des Einlesens, Filterns und Speicherns."""
    kbart_file = select_file("Bitte die KBART-Datei (.tsv) auswählen")
    if not kbart_file:
        return

    purchase_file = select_file("Bitte die Kaufdatei (.xlsx) auswählen")
    if not purchase_file:
        return

    try:
        # 1. Daten laden (utf-8-sig: UTF-8 mit und ohne BOM)
        kbart_df = pd.read_csv(kbart_file, sep='\t', encoding='utf-8-sig')
        if 'publication_type' in kbart_df.columns:
            kbart_df = kbart_df[kbart_df['publication_type'] != 'Serial']
        purchase_df = pd.read_excel(purchase_file)

        # 2. ISBNs extrahieren
        purchase_isbns_set, isbn_columns = extract_isbns_from_purchase_file(purchase_df)
        if not isbn_columns:
            return
        kbart_isbns_set = get_kbart_isbns_as_set(kbart_df)

        # 3. KBART-Datei filtern — normalize_isbns ohne dropna() für korrektes Masking
        online_isbns = normalize_isbns(kbart_df['online_identifier'])
        print_isbns = normalize_isbns(kbart_df['print_identifier'])
        filtered_kbart_df = kbart_df[
            online_isbns.isin(purchase_isbns_set) |
            print_isbns.isin(purchase_isbns_set)
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
                "Ergebnis",
                "Keine Übereinstimmungen gefunden. Die gefilterte KBART-Datei ist leer."
            )

    except pd.errors.ParserError as e:
        messagebox.showerror("Fehler", f"Fehler beim Einlesen der KBART-Datei: {e}")
    except FileNotFoundError as e:
        messagebox.showerror("Fehler", f"Datei nicht gefunden: {e.filename}")
    except KeyError as e:
        messagebox.showerror("Datenfehler", f"Spalte nicht gefunden: {e}")
    except (IndexError, ValueError) as e:
        messagebox.showerror("Datenfehler", f"Ungültiger Wert oder Index: {e}")
    except Exception as e:  # pylint: disable=broad-exception-caught
        messagebox.showerror(
            "Unerwarteter Fehler",
            f"Ein unerwarteter Fehler ist aufgetreten: {type(e).__name__}\n{e}"
        )


# --- GUI-Setup ---

def main() -> None:
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
