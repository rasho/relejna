# Relejna stanica – Upravljanje magacinom

Aplikacija za praćenje stanja u magacinu relejne zaštite. Omogućava kompletno upravljanje inventarom: evidenciju prijema i izdavanja artikala, praćenje kritičnih zaliha, pretragu, filtriranje i izvoz izveštaja.

Navigacija je zasnovana na strelicama (↑ ↓ Enter) — bez kucanja brojeva.

---

## Zahtevi

- Python 3.8+
- SQLite3 (ugrađen u Python)

### Python biblioteke

```
pip install questionary rich reportlab
```

| Biblioteka | Svrha |
|---|---|
| `questionary` | Interaktivna navigacija strelicama |
| `rich` | Bojene tabele i paneli u terminalu |
| `reportlab` | Generisanje PDF izveštaja |

---

## Instalacija

```bash
git clone https://github.com/rasho/relejna.git
cd relejna
pip install questionary rich reportlab
python relejna.py
```

---

## Funkcionalnosti

### Dashboard
- Pregled ukupnog broja artikala i komada na stanju
- Lista artikala koji su ispod kritičnog nivoa
- Pregled poslednje aktivnosti (prijemi i izdavanja)

### Upravljanje artiklima
- Dodavanje novog artikla (Axapta šifra, naziv, količina, kritična količina, lokacija)
- Izmena podataka artikla
- Ažuriranje količine
- Brisanje artikla (soft delete — istorija se čuva)

### Prijem i izdavanje
- Evidencija prijema robe sa datumom i napomenom
- Evidencija izdavanja sa automatskim odbijanjem od stanja
- Upozorenje pri izdavanju ako količina dostiže kritičan nivo
- Istorija svih prijema i izdavanja

### Pretraga i filtriranje
- Pretraga po Axapta šifri ili nazivu
- Filtriranje liste: sve / samo kritične / sortirano po količini ili nazivu

### Izvoz i backup
- Izvoz kompletne liste u CSV
- Izvoz u PDF (kompletna lista ili samo kritični artikli)
- Backup baze podataka sa timestamp-om u nazivu fajla

---

## Baza podataka

Aplikacija koristi SQLite (`artikli.db`). Baza se kreira automatski pri prvom pokretanju. Ako je baza starija verzije, migracija se izvršava automatski bez gubitka podataka.

### Tabele

| Tabela | Opis |
|---|---|
| `Artikli` | Katalog artikala sa stanjem i lokacijom |
| `Izdavanje` | Istorija svih izdavanja |
| `Prijem` | Istorija svih prijema robe |

---

## Autor

[Radenko Bogdanovic](https://github.com/rasho)

## Licenca

[MIT](LICENSE)
