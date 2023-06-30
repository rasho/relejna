import os
import sqlite3
from tabulate import tabulate

# Postavke terminala
os.system("clear" if os.name == "posix" else "cls")

# Kreiranje baze podataka
conn = sqlite3.connect("artikli.db")
c = conn.cursor()

c.execute("""CREATE TABLE IF NOT EXISTS Artikli (
                ID INTEGER PRIMARY KEY AUTOINCREMENT,
                Axapta TEXT,
                Naziv TEXT,
                Kolicina INTEGER,
                KriticnaKolicina INTEGER,
                PoslednjeIzdavanje TEXT
                )""")

c.execute("""CREATE TABLE IF NOT EXISTS Izdavanje (
                ID INTEGER PRIMARY KEY AUTOINCREMENT,
                ArtikalID INTEGER,
                Kolicina INTEGER,
                DatumIzdavanja TEXT
                )""")

conn.commit()


# Prikazuje glavni meni
def prikazi_meni():
    print("=============== GLAVNI MENI ===============")
    print("1. Prikaz liste artikala")
    print("2. Dodavanje novog artikla")
    print("3. Ažuriranje količine artikla")
    print("4. Izdavanje artikla")
    print("5. Prikaz istorije izdavanja artikala")
    print("6. Pretraga artikala")
    print("7. Generisanje izveštaja")
    print("8. Izvoz liste artikala u CSV format")
    print("9. Izvoz liste artikala u PDF format")
    print("10. Izvoz liste artikala sa kritičnom količinom u PDF format")
    print("11. Izlaz")
    print("============================================")


# Prikazuje listu artikala
def prikazi_listu_artikala():
    os.system("clear" if os.name == "posix" else "cls")

    c.execute("SELECT * FROM Artikli")
    artikli = c.fetchall()

    if not artikli:
        print("Nema artikala u bazi.")
    else:
        print("=============== LISTA ARTIKALA ===============")
        print(tabulate(artikli, headers=["ID", "Axapta", "Naziv", "Količina", "Kritična Količina", "Poslednje Izdavanje"]))
        print("==============================================")

    input("Pritisnite Enter za povratak na glavni meni.")


# Dodaje novi artikal
def dodaj_artikal():
    os.system("clear" if os.name == "posix" else "cls")

    axapta = input("Unesite šifru artikla (Axapta): ")
    naziv = input("Unesite naziv artikla: ")
    kolicina = int(input("Unesite početnu količinu artikla: "))
    kriticna_kolicina = int(input("Unesite kritičnu količinu artikla: "))

    c.execute("INSERT INTO Artikli (Axapta, Naziv, Kolicina, KriticnaKolicina) VALUES (?, ?, ?, ?)",
              (axapta, naziv, kolicina, kriticna_kolicina))

    conn.commit()
    print("Artikal je uspešno dodat u bazu.")

    input("Pritisnite Enter za povratak na glavni meni.")


# Ažurira količinu artikla
def azuriraj_kolicinu_artikla():
    os.system("clear" if os.name == "posix" else "cls")

    prikazi_listu_artikala()

    artikal_id = int(input("Unesite ID artikla: "))
    nova_kolicina = int(input("Unesite novu količinu artikla: "))

    c.execute("UPDATE Artikli SET Kolicina = ? WHERE ID = ?", (nova_kolicina, artikal_id))

    conn.commit()
    print("Količina artikla je uspešno ažurirana.")

    input("Pritisnite Enter za povratak na glavni meni.")


# Izdaje artikal
def izdavanje_artikla():
    os.system("clear" if os.name == "posix" else "cls")

    prikazi_listu_artikala()

    artikal_id = int(input("Unesite ID artikla: "))
    kolicina = int(input("Unesite količinu za izdavanje: "))

    c.execute("SELECT Kolicina FROM Artikli WHERE ID = ?", (artikal_id,))
    stara_kolicina = c.fetchone()[0]

    if kolicina > stara_kolicina:
        print("Nema dovoljno artikala na stanju.")
    else:
        nova_kolicina = stara_kolicina - kolicina
        c.execute("UPDATE Artikli SET Kolicina = ? WHERE ID = ?", (nova_kolicina, artikal_id))

        datum_izdavanja = input("Unesite datum izdavanja (dd.mm.gggg): ")
        c.execute("INSERT INTO Izdavanje (ArtikalID, Kolicina, DatumIzdavanja) VALUES (?, ?, ?)",
                  (artikal_id, kolicina, datum_izdavanja))

        conn.commit()
        print("Artikal je uspešno izdat.")

    input("Pritisnite Enter za povratak na glavni meni.")


# Prikazuje istoriju izdavanja artikala
def prikazi_istoriju_izdavanja():
    os.system("clear" if os.name == "posix" else "cls")

    c.execute("""SELECT a.ID, a.Axapta, a.Naziv, i.Kolicina, i.DatumIzdavanja
                 FROM Artikli a
                 INNER JOIN Izdavanje i ON a.ID = i.ArtikalID
                 ORDER BY i.DatumIzdavanja DESC""")
    istorija = c.fetchall()

    if not istorija:
        print("Nema dostupne istorije izdavanja.")
    else:
        print("================= ISTORIJA IZDAVANJA =================")
        print(tabulate(istorija, headers=["ID", "Axapta", "Naziv", "Količina", "Datum Izdavanja"]))
        print("=====================================================")

    input("Pritisnite Enter za povratak na glavni meni.")


# Pretraga artikala
def pretrazi_artikle():
    os.system("clear" if os.name == "posix" else "cls")

    pretraga = input("Unesite pojam za pretragu (šifra artikla, naziv): ")

    c.execute("SELECT * FROM Artikli WHERE Axapta LIKE ? OR Naziv LIKE ?", ('%' + pretraga + '%', '%' + pretraga + '%'))
    rezultati = c.fetchall()

    if not rezultati:
        print("Nema rezultata pretrage.")
    else:
        print("==================== REZULTATI PRETRAGE ====================")
        print(tabulate(rezultati, headers=["ID", "Axapta", "Naziv", "Količina", "Kritična Količina", "Poslednje Izdavanje"]))
        print("===========================================================")

    input("Pritisnite Enter za povratak na glavni meni.")


# Generiše izveštaj o artiklima
def generisi_izvestaj():
    os.system("clear" if os.name == "posix" else "cls")

    c.execute("SELECT * FROM Artikli")
    artikli = c.fetchall()

    if not artikli:
        print("Nema artikala u bazi.")
    else:
        print("============= IZVEŠTAJ O ARTIKLIMA =============")
        print(tabulate(artikli, headers=["ID", "Axapta", "Naziv", "Količina", "Kritična Količina", "Poslednje Izdavanje"]))
        print("================================================")

    input("Pritisnite Enter za povratak na glavni meni.")


# Izvoz liste artikala u CSV format
def export_liste_artikala_csv():
    os.system("clear" if os.name == "posix" else "cls")

    c.execute("SELECT * FROM Artikli")
    artikli = c.fetchall()

    if not artikli:
        print("Nema artikala u bazi.")
    else:
        filename = input("Unesite naziv CSV datoteke za izvoz: ")
        with open(filename, 'w') as file:
            headers = ["ID", "Axapta", "Naziv", "Količina", "Kritična Količina", "Poslednje Izdavanje"]
            file.write(";".join(headers) + "\n")
            for artikal in artikli:
                file.write(";".join([str(value) for value in artikal]) + "\n")

        print("Artikli su uspešno izvezeni u CSV datoteku.")

    input("Pritisnite Enter za povratak na glavni meni.")


# Izvoz liste artikala u PDF format
def export_liste_artikala_pdf():
    os.system("clear" if os.name == "posix" else "cls")

    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas

    c.execute("SELECT * FROM Artikli")
    artikli = c.fetchall()

    if not artikli:
        print("Nema artikala u bazi.")
    else:
        pdf = canvas.Canvas("lista_artikala.pdf", pagesize=letter)

        # Dodajemo header
        header = ["ID", "Axapta", "Naziv", "Količina", "Kritična Količina", "Poslednje Izdavanje"]
        y = 750
        for column, title in enumerate(header):
            pdf.drawString(50 + column * 100, y, title)

        # Dodajemo sadržaj
        y -= 20
        for artikal in artikli:
            for column, value in enumerate(artikal):
                pdf.drawString(50 + column * 100, y, str(value))
            y -= 20

        pdf.save()
        print("Artikli su uspešno izvezeni u PDF datoteku.")

    input("Pritisnite Enter za povratak na glavni meni.")


# Glavna funkcija
def main():
    while True:
        os.system("clear" if os.name == "posix" else "cls")

        prikazi_meni()

        izbor = input("Izaberite opciju (1-11): ")

        if izbor == "1":
            prikazi_listu_artikala()
        elif izbor == "2":
            dodaj_artikal()
        elif izbor == "3":
            azuriraj_kolicinu_artikla()
        elif izbor == "4":
            izdavanje_artikla()
        elif izbor == "5":
            prikazi_istoriju_izdavanja()
        elif izbor == "6":
            pretrazi_artikle()
        elif izbor == "7":
            generisi_izvestaj()
        elif izbor == "8":
            export_liste_artikala_csv()
        elif izbor == "9":
            export_liste_artikala_pdf()
        elif izbor == "10":
            export_liste_artikala_pdf()
        elif izbor == "11":
            break
        else:
            input("Pogrešan izbor. Pritisnite Enter za povratak na glavni meni.")


if __name__ == "__main__":
    main()
