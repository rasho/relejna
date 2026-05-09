import os
import sqlite3
import questionary
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box

console = Console()

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


def obrisi_ekran():
    os.system("clear" if os.name == "posix" else "cls")


def header(naslov):
    console.print(Panel(
        Text(naslov, justify="center", style="bold cyan"),
        border_style="cyan",
        padding=(0, 2)
    ))
    console.print()


def prikazi_listu_artikala():
    obrisi_ekran()
    header("LISTA ARTIKALA")

    c.execute("SELECT * FROM Artikli")
    artikli = c.fetchall()

    if not artikli:
        console.print("[yellow]Nema artikala u bazi.[/yellow]")
    else:
        tabela = Table(box=box.ROUNDED, border_style="cyan", header_style="bold magenta")
        tabela.add_column("ID", style="dim", width=5)
        tabela.add_column("Axapta", style="cyan")
        tabela.add_column("Naziv")
        tabela.add_column("Količina", justify="right")
        tabela.add_column("Kritična kol.", justify="right", style="red")
        tabela.add_column("Poslednje izdavanje", style="dim")

        for a in artikli:
            kol = a[3]
            krit = a[4]
            kol_str = f"[bold red]{kol}[/bold red]" if kol <= krit else f"[green]{kol}[/green]"
            tabela.add_row(str(a[0]), str(a[1] or ""), str(a[2] or ""), kol_str,
                           str(krit), str(a[5] or "-"))

        console.print(tabela)

    console.input("\n[dim]Pritisnite Enter za povratak...[/dim]")


def dodaj_artikal():
    obrisi_ekran()
    header("DODAVANJE NOVOG ARTIKLA")

    axapta = questionary.text("Šifra artikla (Axapta):").ask()
    naziv = questionary.text("Naziv artikla:").ask()
    kolicina = int(questionary.text("Početna količina:").ask())
    kriticna = int(questionary.text("Kritična količina:").ask())

    c.execute("INSERT INTO Artikli (Axapta, Naziv, Kolicina, KriticnaKolicina) VALUES (?, ?, ?, ?)",
              (axapta, naziv, kolicina, kriticna))
    conn.commit()

    console.print("\n[green]✓ Artikal je uspešno dodat u bazu.[/green]")
    console.input("\n[dim]Pritisnite Enter za povratak...[/dim]")


def azuriraj_kolicinu_artikla():
    obrisi_ekran()
    header("AŽURIRANJE KOLIČINE ARTIKLA")

    c.execute("SELECT ID, Axapta, Naziv, Kolicina FROM Artikli")
    artikli = c.fetchall()

    if not artikli:
        console.print("[yellow]Nema artikala u bazi.[/yellow]")
        console.input("\n[dim]Pritisnite Enter za povratak...[/dim]")
        return

    choices = [f"[{a[0]}] {a[1]} – {a[2]}  (trenutno: {a[3]})" for a in artikli]
    choices.append("← Odustani")

    izbor = questionary.select("Izaberite artikal:", choices=choices).ask()

    if izbor == "← Odustani" or izbor is None:
        return

    artikal_id = int(izbor.split("]")[0][1:])
    nova = int(questionary.text("Nova količina:").ask())

    c.execute("UPDATE Artikli SET Kolicina = ? WHERE ID = ?", (nova, artikal_id))
    conn.commit()

    console.print("\n[green]✓ Količina je uspešno ažurirana.[/green]")
    console.input("\n[dim]Pritisnite Enter za povratak...[/dim]")


def izdavanje_artikla():
    obrisi_ekran()
    header("IZDAVANJE ARTIKLA")

    c.execute("SELECT ID, Axapta, Naziv, Kolicina FROM Artikli WHERE Kolicina > 0")
    artikli = c.fetchall()

    if not artikli:
        console.print("[yellow]Nema dostupnih artikala na stanju.[/yellow]")
        console.input("\n[dim]Pritisnite Enter za povratak...[/dim]")
        return

    choices = [f"[{a[0]}] {a[1]} – {a[2]}  (dostupno: {a[3]})" for a in artikli]
    choices.append("← Odustani")

    izbor = questionary.select("Izaberite artikal za izdavanje:", choices=choices).ask()

    if izbor == "← Odustani" or izbor is None:
        return

    artikal_id = int(izbor.split("]")[0][1:])
    c.execute("SELECT Kolicina FROM Artikli WHERE ID = ?", (artikal_id,))
    stara = c.fetchone()[0]

    kolicina = int(questionary.text(f"Količina za izdavanje (max {stara}):").ask())

    if kolicina > stara:
        console.print("\n[red]✗ Nema dovoljno artikala na stanju.[/red]")
    else:
        datum = questionary.text("Datum izdavanja (dd.mm.gggg):").ask()
        nova = stara - kolicina

        c.execute("UPDATE Artikli SET Kolicina = ?, PoslednjeIzdavanje = ? WHERE ID = ?",
                  (nova, datum, artikal_id))
        c.execute("INSERT INTO Izdavanje (ArtikalID, Kolicina, DatumIzdavanja) VALUES (?, ?, ?)",
                  (artikal_id, kolicina, datum))
        conn.commit()

        console.print("\n[green]✓ Artikal je uspešno izdat.[/green]")

    console.input("\n[dim]Pritisnite Enter za povratak...[/dim]")


def prikazi_istoriju_izdavanja():
    obrisi_ekran()
    header("ISTORIJA IZDAVANJA")

    c.execute("""SELECT a.ID, a.Axapta, a.Naziv, i.Kolicina, i.DatumIzdavanja
                 FROM Artikli a
                 INNER JOIN Izdavanje i ON a.ID = i.ArtikalID
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
        tabela.add_column("Datum izdavanja", style="green")

        for red in istorija:
            tabela.add_row(*[str(v or "-") for v in red])

        console.print(tabela)

    console.input("\n[dim]Pritisnite Enter za povratak...[/dim]")


def pretrazi_artikle():
    obrisi_ekran()
    header("PRETRAGA ARTIKALA")

    pretraga = questionary.text("Unesite pojam za pretragu (šifra ili naziv):").ask()

    c.execute("SELECT * FROM Artikli WHERE Axapta LIKE ? OR Naziv LIKE ?",
              (f"%{pretraga}%", f"%{pretraga}%"))
    rezultati = c.fetchall()

    console.print()

    if not rezultati:
        console.print("[yellow]Nema rezultata pretrage.[/yellow]")
    else:
        tabela = Table(box=box.ROUNDED, border_style="magenta", header_style="bold magenta")
        tabela.add_column("ID", style="dim", width=5)
        tabela.add_column("Axapta", style="cyan")
        tabela.add_column("Naziv")
        tabela.add_column("Količina", justify="right", style="green")
        tabela.add_column("Kritična kol.", justify="right", style="red")
        tabela.add_column("Poslednje izdavanje", style="dim")

        for a in rezultati:
            tabela.add_row(*[str(v or "-") for v in a])

        console.print(tabela)

    console.input("\n[dim]Pritisnite Enter za povratak...[/dim]")


def generisi_izvestaj():
    obrisi_ekran()
    header("IZVEŠTAJ O ARTIKLIMA")

    c.execute("SELECT * FROM Artikli")
    artikli = c.fetchall()

    if not artikli:
        console.print("[yellow]Nema artikala u bazi.[/yellow]")
    else:
        kriticni = [a for a in artikli if a[3] <= a[4]]

        console.print(f"  Ukupno artikala:                [bold]{len(artikli)}[/bold]")
        console.print(f"  Artikala ispod kritičnog nivoa: [bold red]{len(kriticni)}[/bold red]\n")

        tabela = Table(box=box.ROUNDED, border_style="green", header_style="bold green")
        tabela.add_column("ID", style="dim", width=5)
        tabela.add_column("Axapta", style="cyan")
        tabela.add_column("Naziv")
        tabela.add_column("Količina", justify="right")
        tabela.add_column("Kritična kol.", justify="right", style="red")
        tabela.add_column("Poslednje izdavanje", style="dim")

        for a in artikli:
            kol = a[3]
            krit = a[4]
            kol_str = f"[bold red]{kol}[/bold red]" if kol <= krit else f"[green]{kol}[/green]"
            tabela.add_row(str(a[0]), str(a[1] or ""), str(a[2] or ""), kol_str,
                           str(krit), str(a[5] or "-"))

        console.print(tabela)

    console.input("\n[dim]Pritisnite Enter za povratak...[/dim]")


def export_csv():
    obrisi_ekran()
    header("IZVOZ U CSV")

    c.execute("SELECT * FROM Artikli")
    artikli = c.fetchall()

    if not artikli:
        console.print("[yellow]Nema artikala u bazi.[/yellow]")
    else:
        filename = questionary.text("Naziv datoteke:").ask()
        if not filename.endswith(".csv"):
            filename += ".csv"

        with open(filename, "w", encoding="utf-8") as f:
            f.write("ID;Axapta;Naziv;Količina;Kritična Količina;Poslednje Izdavanje\n")
            for a in artikli:
                f.write(";".join([str(v or "") for v in a]) + "\n")

        console.print(f"\n[green]✓ Izvezeno u:[/green] [bold]{filename}[/bold]")

    console.input("\n[dim]Pritisnite Enter za povratak...[/dim]")


def export_pdf(samo_kriticni=False):
    obrisi_ekran()
    naslov = "IZVOZ KRITIČNIH ARTIKALA U PDF" if samo_kriticni else "IZVOZ U PDF"
    header(naslov)

    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas as pdf_canvas
    except ImportError:
        console.print("[red]✗ reportlab nije instaliran. Pokrenite: pip install reportlab[/red]")
        console.input("\n[dim]Pritisnite Enter za povratak...[/dim]")
        return

    if samo_kriticni:
        c.execute("SELECT * FROM Artikli WHERE Kolicina <= KriticnaKolicina")
        filename = "kriticni_artikli.pdf"
    else:
        c.execute("SELECT * FROM Artikli")
        filename = "lista_artikala.pdf"

    artikli = c.fetchall()

    if not artikli:
        msg = "Nema artikala sa kritičnom količinom." if samo_kriticni else "Nema artikala u bazi."
        console.print(f"[yellow]{msg}[/yellow]")
    else:
        pdf = pdf_canvas.Canvas(filename, pagesize=letter)
        cols = ["ID", "Axapta", "Naziv", "Količina", "Krit. Kol.", "Poslednje Izdavanje"]
        y = 750
        for i, title in enumerate(cols):
            pdf.drawString(50 + i * 90, y, title)
        y -= 20
        for a in artikli:
            for i, val in enumerate(a):
                pdf.drawString(50 + i * 90, y, str(val or ""))
            y -= 20
            if y < 50:
                pdf.showPage()
                y = 750
        pdf.save()
        console.print(f"\n[green]✓ PDF sačuvan kao:[/green] [bold]{filename}[/bold]")

    console.input("\n[dim]Pritisnite Enter za povratak...[/dim]")


MENI = [
    ("Lista artikala",                    prikazi_listu_artikala),
    ("Dodavanje novog artikla",           dodaj_artikal),
    ("Ažuriranje količine artikla",       azuriraj_kolicinu_artikla),
    ("Izdavanje artikla",                 izdavanje_artikla),
    ("Istorija izdavanja",                prikazi_istoriju_izdavanja),
    ("Pretraga artikala",                 pretrazi_artikle),
    ("Izveštaj",                          generisi_izvestaj),
    ("Izvoz u CSV",                       export_csv),
    ("Izvoz u PDF",                       lambda: export_pdf(False)),
    ("Izvoz kritičnih artikala u PDF",    lambda: export_pdf(True)),
    ("Izlaz",                             None),
]


def main():
    while True:
        obrisi_ekran()

        console.print(Panel(
            "[bold cyan]RELEJNA – UPRAVLJANJE ARTIKLIMA[/bold cyan]",
            subtitle="[dim]↑ ↓  kretanje    Enter  potvrda[/dim]",
            border_style="cyan",
            padding=(1, 4),
        ))

        labels = [naziv for naziv, _ in MENI]
        izbor_label = questionary.select(
            "Izaberite opciju:",
            choices=labels,
            use_shortcuts=False,
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
