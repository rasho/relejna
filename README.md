# Relejna stanica - README

Ovaj projekat predstavlja implementaciju jednostavne aplikacije za praćenje artikala u relejnoj stanici. Aplikacija omogućava upravljanje inventarom artikala, izdavanje artikala, praćenje količina i generisanje izveštaja.

## Prerequisites

- Python 3.x
- SQLite3
- Potrebne biblioteke (instalirajte ih koristeći `pip install` komandu):
  - tabulate
  - reportlab

## Instalacija

1. Klonirajte repozitorijum na vaš lokalni računar.
2. U terminalu ili komandnoj liniji navigirajte do direktorijuma gde je repozitorijum kloniran.
3. Kreirajte virtuelno okruženje (opciono, ali preporučljivo).
4. Instalirajte potrebne biblioteke koristeći `pip install` komandu:
   ```
   pip install tabulate reportlab
   ```

## Upotreba

1. U terminalu ili komandnoj liniji, navigirajte do direktorijuma gde se nalazi projekat.
2. Pokrenite `relejna.py` fajl:
   ```
   python relejna.py
   ```
3. Pratite instrukcije koje se prikazuju na ekranu za korišćenje različitih funkcionalnosti aplikacije.

## Funkcionalnosti

- Prikaz liste artikala
- Dodavanje novog artikla
- Ažuriranje količine artikla
- Izdavanje artikla
- Prikaz istorije izdavanja
- Pretraga artikala
- Generisanje izveštaja o artiklima
- Izvoz liste artikala u CSV format
- Izvoz liste artikala u PDF format
- Izvoz liste artikala sa kritičnom količinom u PDF format

## Autor

- [Radenko Bogdanovic](https://github.com/rasho)

## Licence

Ovaj projekat je licenciran pod [MIT licencom](LICENSE).
