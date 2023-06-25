import sqlite3
from tabulate import tabulate
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter


# Kreiranje baze podataka
def kreiraj_bazu():
    conn = sqlite3.connect("relejna_baza.db")
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
    conn.close()


# Prikaz glavnog menija
def prikazi_meni():
    print("=== Relejna Stanica ===")
    print("1. Prikaz liste artikala")
    print("2. Dodavanje artikla")
    print("3. Ažuriranje količine artikla")
    print("4. Izdavanje artikla")
    print("5. Prikaz istorije izdavanja")
    print("6. Pretraga artikala")
    print("7. Generisanje izveštaja")
    print("8. Izvoz liste artikala u CSV")
    print("9. Izvoz liste artikala u PDF")
    print("10. Izvoz liste artikala sa kritičnom količinom u PDF")
    print("11. Izlaz")


# Prikaz liste artikala
def prikazi_listu_artikala():
    ocisti_ekran()

    c.execute("SELECT * FROM Artikli")
    artikli = c.fetchall()
    if not artikli:
        print("Trenutno nema artikala.")
    else:
        header = ["ID", "Axapta", "Naziv", "Količina", "Kritična Količina", "Poslednje Izdavanje"]
        artikli_tablica = []
        for artikal in artikli:
            artikal_id, axapta, naziv, kolicina, kriticna_kolicina, poslednje_izdavanje = artikal
            artikli_tablica.append(
                [artikal_id, axapta, naziv, kolicina, kriticna_kolicina, poslednje_izdavanje])

        print(tabulate(artikli_tablica, headers=header, tablefmt="grid"))

    input("\nPritisnite Enter za povratak na glavni meni.")


# Dodavanje novog artikla
def dodaj_artikal():
    ocisti_ekran()
    axapta = input("Unesite Axapta broj artikla: ")
    naziv = input("Unesite naziv artikla: ")
    kolicina = int(input("Unesite količinu artikla: "))
    kriticna_kolicina = int(input("Unesite kritičnu količinu artikla: "))
    poslednje_izdavanje = ""

    c.execute("INSERT INTO Artikli (Axapta, Naziv, Kolicina, KriticnaKolicina, PoslednjeIzdavanje) VALUES (?, ?, ?, ?, ?)",
              (axapta, naziv, kolicina, kriticna_kolicina, poslednje_izdavanje))
    conn.commit()

    print("\nArtikal uspešno dodat u bazu podataka.")

    input("\nPritisnite Enter za povratak na glavni meni.")


# Ažuriranje količine artikla
def azuriraj_kolicinu_artikla():
    ocisti_ekran()
    artikal_id = int(input("Unesite ID artikla: "))
    nova_kolicina = int(input("Unesite novu količinu artikla: "))

    c.execute("UPDATE Artikli SET Kolicina = ? WHERE ID = ?", (nova_kolicina, artikal_id))
    conn.commit()

    print("\nKoličina artikla uspešno ažurirana.")

    input("\nPritisnite Enter za povratak na glavni meni.")


# Izdavanje artikla
def izdavanje_artikla():
    ocisti_ekran()
    artikal_id = int(input("Unesite ID artikla: "))
    kolicina = int(input("Unesite količinu za izdavanje: "))
    datum_izdavanja = datetime.now().strftime("%d.%m.%Y %H:%M:%S")

    c.execute("SELECT Kolicina FROM Artikli WHERE ID = ?", (artikal_id,))
    stara_kolicina = c.fetchone()[0]
    nova_kolicina = stara_kolicina - kolicina

    if nova_kolicina >= 0:
        c.execute("UPDATE Artikli SET Kolicina = ?, PoslednjeIzdavanje = ? WHERE ID = ?",
                  (nova_kolicina, datum_izdavanja, artikal_id))
        c.execute("INSERT INTO Izdavanje (ArtikalID, Kolicina, DatumIzdavanja) VALUES (?, ?, ?)",
                  (artikal_id, kolicina, datum_izdavanja))
        conn.commit()
        print("\nArtikal uspešno izdat.")
    else:
        print("\nNedovoljna količina artikla za izdavanje.")

    input("\nPritisnite Enter za povratak na glavni meni.")


# Prikaz istorije izdavanja artikala
def prikazi_istoriju_izdavanja():
    ocisti_ekran()

    c.execute("SELECT * FROM Izdavanje")
    izdavanja = c.fetchall()
    if not izdavanja:
        print("Trenutno nema istorije izdavanja artikala.")
    else:
        header = ["ID", "Artikal ID", "Količina", "Datum izdavanja"]
        izdavanja_tablica = []
        for izdavanje in izdavanja:
            izdavanje_id, artikal_id, kolicina, datum_izdavanja = izdavanje
            izdavanja_tablica.append([izdavanje_id, artikal_id, kolicina, datum_izdavanja])

        print(tabulate(izdavanja_tablica, headers=header, tablefmt="grid"))

    input("\nPritisnite Enter za povratak na glavni meni.")


# Pretraga artikala
def pretraga_artikala():
    ocisti_ekran()
    pretraga = input("Unesite kriterijum pretrage: ")

    c.execute("SELECT * FROM Artikli WHERE Axapta LIKE ? OR Naziv LIKE ?", ('%' + pretraga + '%', '%' + pretraga + '%'))
    artikli = c.fetchall()

    if not artikli:
        print("Nema rezultata pretrage.")
    else:
        header = ["ID", "Axapta", "Naziv", "Količina", "Kritična Količina", "Poslednje Izdavanje"]
        artikli_tablica = []
        for artikal in artikli:
            artikal_id, axapta, naziv, kolicina, kriticna_kolicina, poslednje_izdavanje = artikal
            artikli_tablica.append(
                [artikal_id, axapta, naziv, kolicina, kriticna_kolicina, poslednje_izdavanje])

        print(tabulate(artikli_tablica, headers=header, tablefmt="grid"))

    input("\nPritisnite Enter za povratak na glavni meni.")


# Generisanje izveštaja
def generisi_izvestaj():
    ocisti_ekran()

    c.execute("SELECT * FROM Artikli")
    artikli = c.fetchall()
    if not artikli:
        print("Trenutno nema artikala za generisanje izveštaja.")
        input("\nPritisnite Enter za povratak na glavni meni.")
        return

    header = ["ID", "Axapta", "Naziv", "Količina", "Kritična Količina"]
    artikli_tablica = []
    for artikal in artikli:
        artikal_id, axapta, naziv, kolicina, kriticna_kolicina, _ = artikal
        artikli_tablica.append([artikal_id, axapta, naziv, kolicina, kriticna_kolicina])

    print(tabulate(artikli_tablica, headers=header, tablefmt="grid"))

    opcija = input("\nDa li želite da izvezete izveštaj u PDF? (da/ne): ")
    if opcija.lower() == "da":
        export_izvestaja_pdf(artikli_tablica)


# Izvoz liste artikala u CSV
def export_liste_artikala_csv():
    ocisti_ekran()

    c.execute("SELECT * FROM Artikli")
    artikli = c.fetchall()
    if not artikli:
        print("Trenutno nema artikala za izvoz u CSV.")
        input("\nPritisnite Enter za povratak na glavni meni.")
        return

    header = ["ID", "Axapta", "Naziv", "Količina", "Kritična Količina"]
    artikli_tablica = []
    for artikal in artikli:
        artikal_id, axapta, naziv, kolicina, kriticna_kolicina, _ = artikal
        artikli_tablica.append([artikal_id, axapta, naziv, kolicina, kriticna_kolicina])

    filename = "lista_artikala.csv"
    with open(filename, "w") as file:
        file.write(tabulate(artikli_tablica, headers=header, tablefmt="csv"))

    print(f"\nLista artikala je uspešno izvezena u CSV fajl: {filename}")

    input("\nPritisnite Enter za povratak na glavni meni.")


# Izvoz liste artikala u PDF
def export_liste_artikala_pdf():
    ocisti_ekran()

    c.execute("SELECT * FROM Artikli")
    artikli = c.fetchall()
    if not artikli:
        print("Trenutno nema artikala za izvoz u PDF.")
        input("\nPritisnite Enter za povratak na glavni meni.")
        return

    header = ["ID", "Axapta", "Naziv", "Kolicina", "Kriticna kolicina", "Poslednje Izdavanje"]
    artikli_tablica = []
    for artikal in artikli:
        artikal_id, axapta, naziv, kolicina, kriticna_kolicina, poslednje_izdavanje = artikal
        artikli_tablica.append(
            [artikal_id, axapta, naziv, kolicina, kriticna_kolicina, poslednje_izdavanje])

    pdf_filename = "lista_artikala.pdf"
    pdf = canvas.Canvas(pdf_filename, pagesize=letter)
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(250, 770, "Lista artikala")
    pdf.setFont("Helvetica", 10)

    y = 720
    # Prikaz headera
    for i in range(len(header)):
        pdf.drawString(50 + i * 100, y, header[i])
    y -= 20

    for artikal in artikli_tablica:
        for i in range(len(artikal)):
            pdf.drawString(50 + i * 100, y, str(artikal[i]))
        y -= 20

    pdf.save()

    print(f"\nLista artikala je uspešno izvezena u PDF fajl: {pdf_filename}")

    input("\nPritisnite Enter za povratak na glavni meni.")


# Izvoz liste artikala sa kritičnom količinom u PDF
def export_liste_artikala_kriticna_kolicina_pdf():
    ocisti_ekran()

    c.execute("SELECT * FROM Artikli WHERE Kolicina <= KriticnaKolicina")
    artikli = c.fetchall()
    if not artikli:
        print("Trenutno nema artikala sa kritičnom količinom za izvoz u PDF.")
        input("\nPritisnite Enter za povratak na glavni meni.")
        return

    header = ["ID", "Axapta", "Naziv", "Količina", "Kritična Količina", "Poslednje Izdavanje"]
    artikli_tablica = []
    for artikal in artikli:
        artikal_id, axapta, naziv, kolicina, kriticna_kolicina, poslednje_izdavanje = artikal
        artikli_tablica.append(
            [artikal_id, axapta, naziv, kolicina, kriticna_kolicina, poslednje_izdavanje])

    pdf_filename = "lista_artikala_kriticna_kolicina.pdf"
    pdf = canvas.Canvas(pdf_filename, pagesize=letter)
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(250, 770, "Lista artikala sa kritičnom količinom")
    pdf.setFont("Helvetica", 10)

    y = 720
    for artikal in artikli_tablica:
        for i in range(len(artikal)):
            pdf.drawString(50 + i * 100, y, str(artikal[i]))
        y -= 20

    pdf.save()

    print(f"\nLista artikala sa kritičnom količinom je uspešno izvezena u PDF fajl: {pdf_filename}")

    input("\nPritisnite Enter za povratak na glavni meni.")


# Pomoćna funkcija za čišćenje ekrana
def ocisti_ekran():
    print("\033c", end="")


# Pomoćna funkcija za izvoz liste artikala u PDF
def export_izvestaja_pdf(artikli_tablica):
    pdf_filename = "izvestaj.pdf"
    pdf = canvas.Canvas(pdf_filename, pagesize=letter)
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(250, 770, "Izveštaj o artiklima")
    pdf.setFont("Helvetica", 10)

    y = 720
    for artikal in artikli_tablica:
        for i in range(len(artikal)):
            pdf.drawString(50 + i * 100, y, str(artikal[i]))
        y -= 20

    pdf.save()

    print(f"\nIzveštaj o artiklima je uspešno generisan u PDF fajl: {pdf_filename}")


# Glavni deo programa
conn = sqlite3.connect("relejna_baza.db")
c = conn.cursor()

kreiraj_bazu()

while True:
    ocisti_ekran()
    prikazi_meni()

    izbor = input("\nUnesite broj željene opcije: ")

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
        pretraga_artikala()
    elif izbor == "7":
        generisi_izvestaj()
    elif izbor == "8":
        export_liste_artikala_csv()
    elif izbor == "9":
        export_liste_artikala_pdf()
    elif izbor == "10":
        export_liste_artikala_kriticna_kolicina_pdf()
    elif izbor == "11":
        break

conn.close()
