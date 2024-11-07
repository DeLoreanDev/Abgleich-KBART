import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog

def select_file():
    file_path = filedialog.askopenfilename()
    return file_path

def save_file(dataframe):
    file_path = filedialog.asksaveasfilename(defaultextension=".tsv", filetypes=[("TSV files", "*.tsv")])
    if file_path:
        dataframe.to_csv(file_path, sep='\t', index=False)
        messagebox.showinfo("Gespeichert", f"Gefilterte Datei wurde gespeichert als: {file_path}")

def filter_kbart():
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
    isbn_column_number = simpledialog.askinteger("ISBN-Spalte", "Bitte Spaltennummer der ISBN in der Kaufdatei angeben (beginnend bei 1):")
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

        # Spalte anhand der Nummer auswählen und ISBNs normalisieren (Bindestriche entfernen und als String formatieren)
        isbn_column_purchase = purchase_df.columns[isbn_column_number - 1]  # Umwandlung zur Spaltennummer
        kbart_df['normalized_isbn'] = kbart_df['online_identifier'].astype(str).str.replace('-', '').str.replace('.0', '', regex=False)
        purchase_df['normalized_isbn'] = purchase_df[isbn_column_purchase].astype(str).str.replace('-', '').str.replace('.0', '', regex=False)

        # Gefilterte Datensätze und fehlende ISBNs ermitteln
        filtered_kbart_df = kbart_df[kbart_df['normalized_isbn'].isin(purchase_df['normalized_isbn'])]
        missing_isbns = purchase_df[~purchase_df['normalized_isbn'].isin(kbart_df['normalized_isbn'])]['normalized_isbn'].tolist()

        # Ergebnis anzeigen
        if missing_isbns:
            messagebox.showinfo("Fehlende ISBNs", f"ISBNs aus Kaufdatei, die nicht in KBART-Datei vorkommen:\n{', '.join(missing_isbns)}")
        else:
            messagebox.showinfo("Ergebnis", "Alle ISBNs aus der Kaufdatei sind in der KBART-Datei vorhanden.")

        # Gefilterte Datensätze speichern
        if not filtered_kbart_df.empty:
            save_file(filtered_kbart_df)

    except Exception as e:
        messagebox.showerror("Fehler", f"Ein Fehler ist aufgetreten: {e}")

# GUI-Fenster erstellen
root = tk.Tk()
root.title("KBART Filter Tool")

label = tk.Label(root, text="KBART und Titellisten-Filter", font=("Helvetica", 16))
label.pack(pady=10)

button = tk.Button(root, text="Abgleich starten", command=filter_kbart, font=("Helvetica", 12))
button.pack(pady=10)

info_label = tk.Label(root, text="Bitte wählen Sie zunächst die KBART-Datei und dann die Titelliste aus.", font=("Helvetica", 10))
info_label.pack(pady=10)

root.mainloop()
