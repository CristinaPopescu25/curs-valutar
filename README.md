# 💱 Convertor valutar (BNR + BCE)

Aplicație web care convertește valute folosind **cursurile oficiale** ale Băncii Naționale a României și ale Băncii Centrale Europene.

## La ce ajută

- convertește rapid sume între monede, la cursul oficial actualizat zilnic;
- arată evoluția cursului și cursurile populare, într-o interfață lizibilă pe telefon;
- se deschide direct în browser, fără instalare sau cont.

## Cum a fost făcută

- **Python + Streamlit** pentru interfață: dashboard dark cu tab-uri BNR/BCE, card cu rezultatul conversiei, grafic de linie și listă de valute cu steaguri.
- Datele vin din feedurile oficiale BNR (`curs.bnr.ro/nbrfxrates.xml` și `nbrfxrates10days.xml`) și din API-ul [Frankfurter](https://frankfurter.dev/) (cursuri de referință BCE). Nu este nevoie de cheie API.
- `rates.py` normalizează cursurile (inclusiv `multiplier` pentru monede precum HUF sau JPY), face conversia și trece automat pe cealaltă sursă dacă una nu răspunde.
- Cursul se păstrează în cache o oră, istoricul șase ore; graficul este construit cu Altair.
