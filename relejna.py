import os
import sqlite3
import shutil
from datetime import datetime
import questionary
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box

console = Console()
DB_PATH = "artikli.db"
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()


def init_db():
    c.execute("""CREATE TABLE IF NOT EXISTS Artikli (
        ID INTEGER PRIMARY KEY AUTOINCREMENT,
        Axapta TEXT, Naziv TEXT,
        Kolicina INTEGER DEFAULT 0,
        KriticnaKolicina INTEGER DEFAULT 0,
        PoslednjeIzdavanje TEXT,
        Lokacija TEXT,
        Aktivan INTEGER DEFAULT 1
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS Izdavanje (
        ID INTEGER PRIMARY KEY AUTOINCREMENT,
        ArtikalID INTEGER, Kolicina INTEGER,
        DatumIzdavanja TEXT, Napomena TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS Prijem (
        ID INTEGER PRIMARY KEY AUTOINCREMENT,
        ArtikalID INTEGER, Kolicina INTEGER,
        DatumPrijema TEXT, Napomena TEXT
    )""")

    # Migracija: dodaj kolone ako ne postoje
    existing = {r[1] for r in c.execute("PRAGMA table_info(Artikli)")}
    if "Lokacija" not in existing:
        c.execute("ALTER TABLE Artikli ADD COLUMN Lokacija TEXT")
    if "Aktivan" not in existing:
        c.execute("ALTER TABLE Artikli ADD COLUMN Aktivan INTEGER DEFAULT 1")
        c.execute("UPDATE Artikli SET Aktivan = 1 WHERE Aktivan IS NULL")

    izdavanje_cols = {r[1] for r in c.execute("PRAGMA table_info(Izdavanje)")}
    if "Napomena" not in izdavanje_cols:
        c.execute("ALTER TABLE Izdavanje ADD COLUMN Napomena TEXT")

    conn.commit()


def obrisi_ekran():
    os.system("clear" if os.name == "posix" else "cls")


def header(naslov, subtitle=None):
    console.print(Panel(
        Text(naslov, justify="center", style="bold cyan"),
        border_style="cyan", padding=(0, 2), subtitle=subtitle
    ))
    console.print()


def napravi_tabelu_artikala(artikli, border="cyan"):
    tabela = Table(box=box.ROUNDED, border_style=border, header_style="bold magenta")
    tabela.add_column("ID", style="dim", width=5)
    tabela.add_column("Axapta", style="cyan")
    tabela.add_column("Naziv")
    tabela.add_column("Količina", justify="right")
    tabela.add_column("Kritična kol.", justify="right", style="red")
    tabela.add_column("Lokacija", style="dim")
    tabela.add_column("Poslednje izdavanje", style="dim")
    for a in artikli:
        kol, krit = a[3], a[4]
        kol_str = f"[bold red]{kol}[/bold red]" if kol <= krit else f"[green]{kol}[/green]"
        tabela.add_row(
            str(a[0]), str(a[1] or ""), str(a[2] or ""),
            kol_str, str(krit), str(a[6] or "-"), str(a[5] or "-")
        )
    return tabela


# ─── DASHBOARD ────────────────────────────────────────────────────────────────

def dashboard():
    obrisi_ekran()

    c.execute("SELECT COUNT(*) FROM Artikli WHERE Aktivan = 1")
    ukupno = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM Artikli WHERE Aktivan = 1 AND Kolicina <= KriticnaKolicina")
    kriticnih = c.fetchone()[0]
    c.execute("SELECT COALESCE(SUM(Kolicina), 0) FROM Artikli WHERE Aktivan = 1")
    ukupno_kom = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM Izdavanje")
    ukupno_izdavanja = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM Prijem")
    ukupno_prijema = c.fetchone()[0]

    krit_color = "bold red" if kriticnih > 0 else "green"
    stats = (
        f"  Artikala u sistemu:      [bold]{ukupno}[/bold]\n"
        f"  Ukupno na stanju:        [bold]{ukupno_kom} kom[/bold]\n"
        f"  Ispod kritičnog nivoa:   [{krit_color}]{kriticnih}[/{krit_color}]\n"
        f"  Evidentiranih izdavanja: [bold]{ukupno_izdavanja}[/bold]\n"
        f"  Evidentiranih prijema:   [bold]{ukupno_prijema}[/bold]"
    )
    console.print(Panel(stats, title="[bold]Pregled sistema[/bold]",
                        border_style="blue", padding=(1, 2)))
    console.print()

    # Poslednja aktivnost
    c.execute("""
        SELECT a.Naziv, i.Kolicina, i.DatumIzdavanja, 'Izdavanje'
        FROM Izdavanje i JOIN Artikli a ON a.ID = i.ArtikalID
        UNION ALL
        SELECT a.Naziv, p.Kolicina, p.DatumPrijema, 'Prijem'
        FROM Prijem p JOIN Artikli a ON a.ID = p.ArtikalID
        ORDER BY 3 DESC LIMIT 6
    """)
    aktivnost = c.fetchall()

    if aktivnost:
        tabela = Table(box=box.SIMPLE, header_style="bold", border_style="dim")
        tabela.add_column("Artikal")
        tabela.add_column("Količina", justify="right")
        tabela.add_column("Datum")
        tabela.add_column("Tip")
        for red in aktivnost:
            tip_style = "green" if red[3] == "Prijem" else "yellow"
            tabela.add_row(str(red[0] or ""), str(red[1]), str(red[2] or ""),
                           f"[{tip_style}]{red[3]}[/{tip_style}]")
        console.print(Panel(tabela, title="[bold]Poslednja aktivnost[/bold]",
                            border_style="blue", padding=(0, 1)))
        console.print()

    # Upozorenje za kritične
    if kriticnih > 0:
        c.execute("""SELECT Axapta, Naziv, Kolicina, KriticnaKolicina, Lokacija
                     FROM Artikli WHERE Aktivan = 1 AND Kolicina <= KriticnaKolicina""")
        kriticni_artikli = c.fetchall()
        warn = Table(box=box.SIMPLE, header_style="bold red", border_style="red")
        warn.add_column("Axapta", style="cyan")
        warn.add_column("Naziv")
        warn.add_column("Na stanju", justify="right", style="bold red")
        warn.add_column("Kritična kol.", justify="right")
        warn.add_column("Lokacija", style="dim")
        for a in kriticni_artikli:
            warn.add_row(str(a[0] or ""), str(a[1] or ""), str(a[2]),
                         str(a[3]), str(a[4] or "-"))
        console.print(Panel(warn, title="[bold red]ARTIKLI ISPOD KRITIČNOG NIVOA[/bold red]",
                            border_style="red", padding=(0, 1)))
        console.print()

    console.input("[dim]Pritisnite Enter za povratak...[/dim]")


# ─── ARTIKLI ──────────────────────────────────────────────────────────────────

def prikazi_listu_artikala():
    obrisi_ekran()
    header("LISTA ARTIKALA")

    filter_izbor = questionary.select(
        "Prikaz:",
        choices=[
            "Sve artikle",
            "Samo kritične",
            "Sortirano po količini ↑",
            "Sortirano po količini ↓",
            "Sortirano po nazivu",
        ]
    ).ask()

    if filter_izbor is None:
        return

    base = """SELECT ID, Axapta, Naziv, Kolicina, KriticnaKolicina,
                     PoslednjeIzdavanje, Lokacija
              FROM Artikli WHERE Aktivan = 1"""

    extras = {
        "Samo kritične":          " AND Kolicina <= KriticnaKolicina",
        "Sortirano po količini ↑": " ORDER BY Kolicina ASC",
        "Sortirano po količini ↓": " ORDER BY Kolicina DESC",
        "Sortirano po nazivu":    " ORDER BY Naziv ASC",
    }
    c.execute(base + extras.get(filter_izbor, ""))
    artikli = c.fetchall()

    obrisi_ekran()
    header("LISTA ARTIKALA", subtitle=f"[dim]{filter_izbor}[/dim]")

    if not artikli:
        console.print("[yellow]Nema artikala za prikaz.[/yellow]")
    else:
        console.print(napravi_tabelu_artikala(artikli))

    console.input("\n[dim]Pritisnite Enter za povratak...[/dim]")


def dodaj_artikal():
    obrisi_ekran()
    header("DODAVANJE NOVOG ARTIKLA")

    axapta = questionary.text("Šifra artikla (Axapta):").ask()
    naziv = questionary.text("Naziv artikla:").ask()
    kolicina = int(questionary.text("Početna količina:").ask())
    kriticna = int(questionary.text("Kritična količina:").ask())
    lokacija = questionary.text("Lokacija u magacinu (opciono):").ask()

    c.execute("""INSERT INTO Artikli (Axapta, Naziv, Kolicina, KriticnaKolicina, Lokacija)
                 VALUES (?, ?, ?, ?, ?)""",
              (axapta, naziv, kolicina, kriticna, lokacija or None))
    conn.commit()

    console.print("\n[green]✓ Artikal je uspešno dodat.[/green]")
    console.input("\n[dim]Pritisnite Enter za povratak...[/dim]")


def izmeni_artikal():
    obrisi_ekran()
    header("IZMENA ARTIKLA")

    c.execute("SELECT ID, Axapta, Naziv FROM Artikli WHERE Aktivan = 1")
    artikli = c.fetchall()

    if not artikli:
        console.print("[yellow]Nema artikala u bazi.[/yellow]")
        console.input("\n[dim]Pritisnite Enter za povratak...[/dim]")
        return

    choices = [f"[{a[0]}] {a[1]} – {a[2]}" for a in artikli] + ["← Odustani"]
    izbor = questionary.select("Izaberite artikal za izmenu:", choices=choices).ask()

    if izbor is None or izbor == "← Odustani":
        return

    artikal_id = int(izbor.split("]")[0][1:])
    c.execute("SELECT Axapta, Naziv, KriticnaKolicina, Lokacija FROM Artikli WHERE ID = ?",
              (artikal_id,))
    a = c.fetchone()

    obrisi_ekran()
    header("IZMENA ARTIKLA")
    console.print("[dim]Ostavite prazno da zadržite postojeću vrednost.[/dim]\n")

    axapta = questionary.text(f"Axapta [{a[0]}]:").ask() or a[0]
    naziv = questionary.text(f"Naziv [{a[1]}]:").ask() or a[1]
    krit_str = questionary.text(f"Kritična količina [{a[2]}]:").ask()
    kriticna = int(krit_str) if krit_str else a[2]
    lok_str = questionary.text(f"Lokacija [{a[3] or '-'}]:").ask()
    lokacija = lok_str if lok_str else a[3]

    c.execute("""UPDATE Artikli SET Axapta = ?, Naziv = ?, KriticnaKolicina = ?, Lokacija = ?
                 WHERE ID = ?""", (axapta, naziv, kriticna, lokacija, artikal_id))
    conn.commit()

    console.print("\n[green]✓ Artikal je uspešno izmenjen.[/green]")
    console.input("\n[dim]Pritisnite Enter za povratak...[/dim]")


def obrisi_artikal():
    obrisi_ekran()
    header("BRISANJE ARTIKLA")

    c.execute("SELECT ID, Axapta, Naziv, Kolicina FROM Artikli WHERE Aktivan = 1")
    artikli = c.fetchall()

    if not artikli:
        console.print("[yellow]Nema artikala u bazi.[/yellow]")
        console.input("\n[dim]Pritisnite Enter za povratak...[/dim]")
        return

    choices = [f"[{a[0]}] {a[1]} – {a[2]} (stanje: {a[3]})" for a in artikli] + ["← Odustani"]
    izbor = questionary.select("Izaberite artikal za brisanje:", choices=choices).ask()

    if izbor is None or izbor == "← Odustani":
        return

    artikal_id = int(izbor.split("]")[0][1:])
    naziv = next(a[2] for a in artikli if a[0] == artikal_id)

    potvrda = questionary.confirm(
        f"Arhivirati '{naziv}'? (istorija izdavanja/prijema se čuva)"
    ).ask()

    if potvrda:
        c.execute("UPDATE Artikli SET Aktivan = 0 WHERE ID = ?", (artikal_id,))
        conn.commit()
        console.print("\n[green]✓ Artikal je arhiviran.[/green]")
    else:
        console.print("\n[dim]Akcija otkazana.[/dim]")

    console.input("\n[dim]Pritisnite Enter za povratak...[/dim]")


def azuriraj_kolicinu_artikla():
    obrisi_ekran()
    header("AŽURIRANJE KOLIČINE ARTIKLA")

    c.execute("SELECT ID, Axapta, Naziv, Kolicina FROM Artikli WHERE Aktivan = 1")
    artikli = c.fetchall()

    if not artikli:
        console.print("[yellow]Nema artikala u bazi.[/yellow]")
        console.input("\n[dim]Pritisnite Enter za povratak...[/dim]")
        return

    choices = [f"[{a[0]}] {a[1]} – {a[2]}  (trenutno: {a[3]})" for a in artikli] + ["← Odustani"]
    izbor = questionary.select("Izaberite artikal:", choices=choices).ask()

    if izbor is None or izbor == "← Odustani":
        return

    artikal_id = int(izbor.split("]")[0][1:])
    nova = int(questionary.text("Nova količina:").ask())

    c.execute("UPDATE Artikli SET Kolicina = ? WHERE ID = ?", (nova, artikal_id))
    conn.commit()

    console.print("\n[green]✓ Količina je uspešno ažurirana.[/green]")
    console.input("\n[dim]Pritisnite Enter za povratak...[/dim]")


# ─── PRIJEM / IZDAVANJE ───────────────────────────────────────────────────────

def prijem_robe():
    obrisi_ekran()
    header("PRIJEM ROBE")

    c.execute("SELECT ID, Axapta, Naziv, Kolicina FROM Artikli WHERE Aktivan = 1")
    artikli = c.fetchall()

    if not artikli:
        console.print("[yellow]Nema artikala u bazi.[/yellow]")
        console.input("\n[dim]Pritisnite Enter za povratak...[/dim]")
        return

    choices = [f"[{a[0]}] {a[1]} – {a[2]}  (stanje: {a[3]})" for a in artikli] + ["← Odustani"]
    izbor = questionary.select("Izaberite artikal:", choices=choices).ask()

    if izbor is None or izbor == "← Odustani":
        return

    artikal_id = int(izbor.split("]")[0][1:])
    kolicina = int(questionary.text("Primljena količina:").ask())
    datum = questionary.text("Datum prijema (dd.mm.gggg):").ask()
    napomena = questionary.text("Napomena (opciono):").ask()

    c.execute("UPDATE Artikli SET Kolicina = Kolicina + ? WHERE ID = ?", (kolicina, artikal_id))
    c.execute("INSERT INTO Prijem (ArtikalID, Kolicina, DatumPrijema, Napomena) VALUES (?, ?, ?, ?)",
              (artikal_id, kolicina, datum, napomena or None))
    conn.commit()

    console.print(f"\n[green]✓ Prijem evidentiran. Primljeno: {kolicina} kom.[/green]")
    console.input("\n[dim]Pritisnite Enter za povratak...[/dim]")


def izdavanje_artikla():
    obrisi_ekran()
    header("IZDAVANJE ARTIKLA")

    c.execute("SELECT ID, Axapta, Naziv, Kolicina FROM Artikli WHERE Aktivan = 1 AND Kolicina > 0")
    artikli = c.fetchall()

    if not artikli:
        console.print("[yellow]Nema dostupnih artikala na stanju.[/yellow]")
        console.input("\n[dim]Pritisnite Enter za povratak...[/dim]")
        return

    choices = [f"[{a[0]}] {a[1]} – {a[2]}  (dostupno: {a[3]})" for a in artikli] + ["← Odustani"]
    izbor = questionary.select("Izaberite artikal za izdavanje:", choices=choices).ask()

    if izbor is None or izbor == "← Odustani":
        return

    artikal_id = int(izbor.split("]")[0][1:])
    c.execute("SELECT Kolicina, KriticnaKolicina FROM Artikli WHERE ID = ?", (artikal_id,))
    stara, krit = c.fetchone()

    kolicina = int(questionary.text(f"Količina za izdavanje (max {stara}):").ask())

    if kolicina > stara:
        console.print("\n[red]✗ Nema dovoljno artikala na stanju.[/red]")
    else:
        datum = questionary.text("Datum izdavanja (dd.mm.gggg):").ask()
        napomena = questionary.text("Napomena (opciono):").ask()
        nova = stara - kolicina

        c.execute("UPDATE Artikli SET Kolicina = ?, PoslednjeIzdavanje = ? WHERE ID = ?",
                  (nova, datum, artikal_id))
        c.execute("INSERT INTO Izdavanje (ArtikalID, Kolicina, DatumIzdavanja, Napomena) VALUES (?, ?, ?, ?)",
                  (artikal_id, kolicina, datum, napomena or None))
        conn.commit()

        console.print(f"\n[green]✓ Izdato {kolicina} kom. Novo stanje: {nova} kom.[/green]")

        if nova <= krit:
            console.print("[bold red]  Upozorenje: Količina je dostigla kritičan nivo![/bold red]")

    console.input("\n[dim]Pritisnite Enter za povratak...[/dim]")


# ─── ISTORIJA ─────────────────────────────────────────────────────────────────

def prikazi_istoriju_izdavanja():
    obrisi_ekran()
    header("ISTORIJA IZDAVANJA")

    c.execute("""SELECT a.ID, a.Axapta, a.Naziv, i.Kolicina, i.DatumIzdavanja, i.Napomena
                 FROM Artikli a INNER JOIN Izdavanje i ON a.ID = i.ArtikalID
                 ORDER BY i.DatumIzdavanja DESC""")
    istorija = c.fetchall()

    if not istorija:
        console.print("[yellow]Nema dostupne istorije izdavanja.[/yellow]")
    else:
        tabela = Table(box=box.ROUNDED, border_style="blue", header_style="bold blue")
        tabela.add_column("ID", style="dim", width=5)
        tabela.add_column("Axapta", style="cyan")
        tabela.add_column("Naziv")
        tabela.add_column("Količina", justify="right", style="yellow")
        tabela.add_column("Datum", style="green")
        tabela.add_column("Napomena", style="dim")
        for red in istorija:
            tabela.add_row(*[str(v or "-") for v in red])
        console.print(tabela)

    console.input("\n[dim]Pritisnite Enter za povratak...[/dim]")


def prikazi_istoriju_prijema():
    obrisi_ekran()
    header("ISTORIJA PRIJEMA")

    c.execute("""SELECT a.ID, a.Axapta, a.Naziv, p.Kolicina, p.DatumPrijema, p.Napomena
                 FROM Artikli a INNER JOIN Prijem p ON a.ID = p.ArtikalID
                 ORDER BY p.DatumPrijema DESC""")
    istorija = c.fetchall()

    if not istorija:
        console.print("[yellow]Nema dostupne istorije prijema.[/yellow]")
    else:
        tabela = Table(box=box.ROUNDED, border_style="green", header_style="bold green")
        tabela.add_column("ID", style="dim", width=5)
        tabela.add_column("Axapta", style="cyan")
        tabela.add_column("Naziv")
        tabela.add_column("Količina", justify="right", style="green")
        tabela.add_column("Datum", style="blue")
        tabela.add_column("Napomena", style="dim")
        for red in istorija:
            tabela.add_row(*[str(v or "-") for v in red])
        console.print(tabela)

    console.input("\n[dim]Pritisnite Enter za povratak...[/dim]")


# ─── PRETRAGA / IZVEŠTAJ ──────────────────────────────────────────────────────

def pretrazi_artikle():
    obrisi_ekran()
    header("PRETRAGA ARTIKALA")

    pretraga = questionary.text("Unesite pojam za pretragu (šifra ili naziv):").ask()

    c.execute("""SELECT ID, Axapta, Naziv, Kolicina, KriticnaKolicina,
                        PoslednjeIzdavanje, Lokacija
                 FROM Artikli WHERE Aktivan = 1 AND (Axapta LIKE ? OR Naziv LIKE ?)""",
              (f"%{pretraga}%", f"%{pretraga}%"))
    rezultati = c.fetchall()

    console.print()
    if not rezultati:
        console.print("[yellow]Nema rezultata pretrage.[/yellow]")
    else:
        console.print(napravi_tabelu_artikala(rezultati, border="magenta"))

    console.input("\n[dim]Pritisnite Enter za povratak...[/dim]")


def generisi_izvestaj():
    obrisi_ekran()
    header("IZVEŠTAJ O ARTIKLIMA")

    c.execute("""SELECT ID, Axapta, Naziv, Kolicina, KriticnaKolicina,
                        PoslednjeIzdavanje, Lokacija
                 FROM Artikli WHERE Aktivan = 1""")
    artikli = c.fetchall()

    if not artikli:
        console.print("[yellow]Nema artikala u bazi.[/yellow]")
    else:
        kriticni = [a for a in artikli if a[3] <= a[4]]
        ukupno_kom = sum(a[3] for a in artikli)

        console.print(f"  Ukupno artikala:                [bold]{len(artikli)}[/bold]")
        console.print(f"  Ukupno komada na stanju:        [bold]{ukupno_kom}[/bold]")
        console.print(f"  Artikala ispod kritičnog nivoa: [bold red]{len(kriticni)}[/bold red]\n")
        console.print(napravi_tabelu_artikala(artikli, border="green"))

    console.input("\n[dim]Pritisnite Enter za povratak...[/dim]")


# ─── IZVOZ ────────────────────────────────────────────────────────────────────

def export_csv():
    obrisi_ekran()
    header("IZVOZ U CSV")

    c.execute("""SELECT ID, Axapta, Naziv, Kolicina, KriticnaKolicina,
                        PoslednjeIzdavanje, Lokacija
                 FROM Artikli WHERE Aktivan = 1""")
    artikli = c.fetchall()

    if not artikli:
        console.print("[yellow]Nema artikala u bazi.[/yellow]")
    else:
        filename = questionary.text("Naziv datoteke:", default="lista_artikala").ask()
        if not filename.endswith(".csv"):
            filename += ".csv"
        with open(filename, "w", encoding="utf-8") as f:
            f.write("ID;Axapta;Naziv;Količina;Kritična Količina;Poslednje Izdavanje;Lokacija\n")
            for a in artikli:
                f.write(";".join([str(v or "") for v in a]) + "\n")
        console.print(f"\n[green]✓ Izvezeno u:[/green] [bold]{filename}[/bold]")

    console.input("\n[dim]Pritisnite Enter za povratak...[/dim]")


def export_pdf(samo_kriticni=False):
    obrisi_ekran()
    header("IZVOZ KRITIČNIH ARTIKALA U PDF" if samo_kriticni else "IZVOZ U PDF")

    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas as pdf_canvas
    except ImportError:
        console.print("[red]✗ reportlab nije instaliran. Pokrenite: pip install reportlab[/red]")
        console.input("\n[dim]Pritisnite Enter za povratak...[/dim]")
        return

    if samo_kriticni:
        c.execute("""SELECT ID, Axapta, Naziv, Kolicina, KriticnaKolicina,
                            PoslednjeIzdavanje, Lokacija
                     FROM Artikli WHERE Aktivan = 1 AND Kolicina <= KriticnaKolicina""")
        filename = "kriticni_artikli.pdf"
    else:
        c.execute("""SELECT ID, Axapta, Naziv, Kolicina, KriticnaKolicina,
                            PoslednjeIzdavanje, Lokacija
                     FROM Artikli WHERE Aktivan = 1""")
        filename = "lista_artikala.pdf"

    artikli = c.fetchall()

    if not artikli:
        console.print("[yellow]Nema podataka za izvoz.[/yellow]")
    else:
        pdf = pdf_canvas.Canvas(filename, pagesize=letter)
        cols = ["ID", "Axapta", "Naziv", "Količina", "Krit.Kol.", "Posl.Izd.", "Lokacija"]
        y = 750
        for i, title in enumerate(cols):
            pdf.drawString(50 + i * 78, y, title)
        y -= 20
        for a in artikli:
            for i, val in enumerate(a):
                pdf.drawString(50 + i * 78, y, str(val or ""))
            y -= 20
            if y < 50:
                pdf.showPage()
                y = 750
        pdf.save()
        console.print(f"\n[green]✓ PDF sačuvan kao:[/green] [bold]{filename}[/bold]")

    console.input("\n[dim]Pritisnite Enter za povratak...[/dim]")


# ─── BACKUP ───────────────────────────────────────────────────────────────────

def backup_baze():
    obrisi_ekran()
    header("BACKUP BAZE PODATAKA")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"artikli_backup_{timestamp}.db"

    try:
        shutil.copy2(DB_PATH, backup_name)
        console.print(f"[green]✓ Backup sačuvan kao:[/green] [bold]{backup_name}[/bold]")
    except Exception as e:
        console.print(f"[red]✗ Greška pri backup-u: {e}[/red]")

    console.input("\n[dim]Pritisnite Enter za povratak...[/dim]")


# ─── MENI ─────────────────────────────────────────────────────────────────────

MENI = [
    ("Dashboard",                         dashboard),
    ("Lista artikala",                    prikazi_listu_artikala),
    ("Dodavanje novog artikla",           dodaj_artikal),
    ("Izmena artikla",                    izmeni_artikal),
    ("Brisanje artikla",                  obrisi_artikal),
    ("Ažuriranje količine",               azuriraj_kolicinu_artikla),
    ("Prijem robe",                       prijem_robe),
    ("Izdavanje artikla",                 izdavanje_artikla),
    ("Istorija izdavanja",                prikazi_istoriju_izdavanja),
    ("Istorija prijema",                  prikazi_istoriju_prijema),
    ("Pretraga artikala",                 pretrazi_artikle),
    ("Izveštaj",                          generisi_izvestaj),
    ("Izvoz u CSV",                       export_csv),
    ("Izvoz u PDF",                       lambda: export_pdf(False)),
    ("Izvoz kritičnih artikala u PDF",    lambda: export_pdf(True)),
    ("Backup baze",                       backup_baze),
    ("Izlaz",                             None),
]


def main():
    init_db()

    while True:
        obrisi_ekran()

        console.print(Panel(
            "[bold cyan]RELEJNA – UPRAVLJANJE ARTIKLIMA[/bold cyan]",
            subtitle="[dim]↑ ↓  kretanje    Enter  potvrda[/dim]",
            border_style="cyan", padding=(1, 4),
        ))

        labels = [naziv for naziv, _ in MENI]
        izbor_label = questionary.select(
            "Izaberite opciju:", choices=labels, use_shortcuts=False,
        ).ask()

        if izbor_label is None or izbor_label == "Izlaz":
            obrisi_ekran()
            console.print("[cyan]Doviđenja![/cyan]\n")
            break

        for naziv, akcija in MENI:
            if naziv == izbor_label:
                akcija()
                break


if __name__ == "__main__":
    main()
