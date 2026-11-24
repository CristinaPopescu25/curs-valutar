# 💱 Convertor valutar (BNR + BCE)

Aplicație web simplă, optimizată pentru telefon, care convertește valută folosind
**cursurile oficiale**:

- **BNR** – Banca Națională a României, prin fișierul XML public `https://curs.bnr.ro/nbrfxrates.xml`
  (vechiul URL `www.bnr.ro/nbrfxrates.xml` nu mai este valid din august 2026).
- **BCE** – Banca Centrală Europeană, prin [Frankfurter](https://frankfurter.dev/)
  care republicează cursurile de referință EUR (`https://api.frankfurter.app/latest?from=EUR`).

Nu este necesară nicio cheie API. Cursurile se reîmprospătează la fiecare oră (cache partajat),
pentru a nu supraîncărca serverul BNR. BNR publică cursul nou după ora 13:00, în zilele bancare.
Dacă o sursă nu răspunde, aplicația trece automat pe cealaltă.

## Rulare locală

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Se deschide automat `http://localhost:8501` în browser.

## Publicare gratuită pe Streamlit Cloud (link pentru telefon)

1. Creează un **repo GitHub nou** (poate fi public). Încarcă în el **conținutul acestui folder**
   (`app.py`, `rates.py`, `requirements.txt`, `.streamlit/config.toml`) - nu tot proiectul SkillMatrix.
   din folderul `currency_converter`:

   ```powershell
   git init
   git add .
   git commit -m "Convertor valutar BNR + BCE"
   git remote add origin https://github.com/<user>/<repo>.git
   git push -u origin main
   ```

2. Intră pe [share.streamlit.io](https://share.streamlit.io/) și autentifică-te cu GitHub.
3. Apasă **New app** → alege repo-ul, branch-ul `main` și ca *Main file path* `app.py`.
4. Apasă **Deploy**. După câteva minute primești linkul de forma
   `https://<nume-repo>.streamlit.app`.
5. Deschide linkul pe telefon. Din meniul browserului (Chrome: ⋮, Safari: ⤴)
   alege **Add to Home Screen** pentru icon pe ecranul de start.

> Alternativă: dacă folosești repo-ul existent, poți indica drept *Main file path*
> `currency_converter/app.py`; asigură-te doar că `requirements.txt` de la rădăcina repo-ului
> conține `streamlit` și `requests`.

## Teste

```powershell
python -m unittest discover -s . -p "test_*.py" -v
```

## Note

- Cursurile afișate sunt de referință; băncile pot aplica alte cursuri la tranzacții reale.
- BNR exprimă unele cursuri la `multiplier` unități (ex. HUF la 100), ceea ce aplicația
  normalizează corect în `rates.py`.
- Schema XML BNR și-a schimbat namespace-ul în 2026; parserul ignoră namespace-ul, deci
  funcționează cu ambele variante.
