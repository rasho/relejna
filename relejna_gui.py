import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime
import shutil

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

DB_PATH = "artikli.db"

C_RED    = "#ef4444"
C_GREEN  = "#22c55e"
C_ORANGE = "#f97316"
C_BLUE   = "#3b82f6"
C_DIM    = "#6b7280"


# ─── MAIN APP ─────────────────────────────────────────────────────────────────

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Relejna – Upravljanje artiklima")
        self.geometry("1300x800")
        self.minsize(1050, 650)

        self.conn = sqlite3.connect(DB_PATH)
        self.c = self.conn.cursor()
        self._init_db()
        self._style_treeview()

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_sidebar()
        self._build_main()
        self.navigate("dashboard")

    def _init_db(self):
        self.c.executescript("""
            CREATE TABLE IF NOT EXISTS Artikli (
                ID INTEGER PRIMARY KEY AUTOINCREMENT,
                Axapta TEXT, Naziv TEXT,
                Kolicina INTEGER DEFAULT 0,
                KriticnaKolicina INTEGER DEFAULT 0,
                PoslednjeIzdavanje TEXT,
                Lokacija TEXT,
                Aktivan INTEGER DEFAULT 1
            );
            CREATE TABLE IF NOT EXISTS Izdavanje (
                ID INTEGER PRIMARY KEY AUTOINCREMENT,
                ArtikalID INTEGER, Kolicina INTEGER,
                DatumIzdavanja TEXT, Napomena TEXT
            );
            CREATE TABLE IF NOT EXISTS Prijem (
                ID INTEGER PRIMARY KEY AUTOINCREMENT,
                ArtikalID INTEGER, Kolicina INTEGER,
                DatumPrijema TEXT, Napomena TEXT
            );
        """)
        existing = {r[1] for r in self.c.execute("PRAGMA table_info(Artikli)")}
        if "Lokacija" not in existing:
            self.c.execute("ALTER TABLE Artikli ADD COLUMN Lokacija TEXT")
        if "Aktivan" not in existing:
            self.c.execute("ALTER TABLE Artikli ADD COLUMN Aktivan INTEGER DEFAULT 1")
            self.c.execute("UPDATE Artikli SET Aktivan = 1 WHERE Aktivan IS NULL")
        izd_cols = {r[1] for r in self.c.execute("PRAGMA table_info(Izdavanje)")}
        if "Napomena" not in izd_cols:
            self.c.execute("ALTER TABLE Izdavanje ADD COLUMN Napomena TEXT")
        self.conn.commit()

    def _style_treeview(self):
        s = ttk.Style()
        s.theme_use("default")
        s.configure("T.Treeview",
            background="#2b2b2b", foreground="white", rowheight=30,
            fieldbackground="#2b2b2b", borderwidth=0,
            font=("Segoe UI", 11))
        s.map("T.Treeview",
            background=[("selected", "#1f538d")],
            foreground=[("selected", "white")])
        s.configure("T.Treeview.Heading",
            background="#1a1a1a", foreground="#9ca3af",
            relief="flat", font=("Segoe UI", 11, "bold"))
        s.map("T.Treeview.Heading", background=[("active", "#2b2b2b")])

    # ── Sidebar ───────────────────────────────────────────────────────────────

    def _build_sidebar(self):
        sb = ctk.CTkFrame(self, width=220, corner_radius=0,
                          fg_color=("#ececec", "#1a1a1a"))
        sb.grid(row=0, column=0, sticky="nsew")
        sb.grid_propagate(False)
        sb.grid_rowconfigure(12, weight=1)
        self.sidebar = sb

        logo = ctk.CTkFrame(sb, fg_color="transparent")
        logo.grid(row=0, column=0, padx=18, pady=(22, 8), sticky="w")
        ctk.CTkLabel(logo, text="RELEJNA",
                     font=ctk.CTkFont(size=22, weight="bold")).pack(anchor="w")
        ctk.CTkLabel(logo, text="Upravljanje artiklima",
                     font=ctk.CTkFont(size=11),
                     text_color=C_DIM).pack(anchor="w")

        ctk.CTkFrame(sb, height=1,
                     fg_color=("#d0d0d0", "#333333")).grid(
                     row=1, column=0, sticky="ew", padx=15, pady=(0, 8))

        nav = [
            ("dashboard", "  Dashboard"),
            ("artikli",   "  Artikli"),
            ("prijem",    "  Prijem robe"),
            ("izdavanje", "  Izdavanje"),
            ("istorija",  "  Istorija"),
            ("izvoz",     "  Izvoz & Backup"),
        ]
        self.nav_btns = {}
        for i, (key, label) in enumerate(nav):
            btn = ctk.CTkButton(sb, text=label, anchor="w", height=40,
                fg_color="transparent",
                text_color=("gray15", "gray90"),
                hover_color=("gray80", "gray25"),
                corner_radius=8, font=ctk.CTkFont(size=13),
                command=lambda k=key: self.navigate(k))
            btn.grid(row=i + 2, column=0, padx=10, pady=2, sticky="ew")
            self.nav_btns[key] = btn

        ctk.CTkLabel(sb, text="Tema", text_color=C_DIM,
                     font=ctk.CTkFont(size=11)).grid(
                     row=13, column=0, padx=18, pady=(10, 2), sticky="w")
        ctk.CTkOptionMenu(sb, values=["Dark", "Light", "System"],
                          height=32, font=ctk.CTkFont(size=12),
                          command=lambda v: ctk.set_appearance_mode(v)).grid(
                          row=14, column=0, padx=10, pady=(0, 18), sticky="ew")

    def _build_main(self):
        self.main = ctk.CTkFrame(self, fg_color="transparent")
        self.main.grid(row=0, column=1, sticky="nsew", padx=15, pady=15)
        self.main.grid_columnconfigure(0, weight=1)
        self.main.grid_rowconfigure(0, weight=1)
        self.current_frame = None

    def navigate(self, key):
        for k, btn in self.nav_btns.items():
            btn.configure(fg_color=("gray80", "gray25") if k == key else "transparent")
        if self.current_frame:
            self.current_frame.destroy()
            self.current_frame = None
        {
            "dashboard": self._view_dashboard,
            "artikli":   self._view_artikli,
            "prijem":    self._view_prijem,
            "izdavanje": self._view_izdavanje,
            "istorija":  self._view_istorija,
            "izvoz":     self._view_izvoz,
        }[key]()

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _page_title(self, parent, title):
        ctk.CTkLabel(parent, text=title,
                     font=ctk.CTkFont(size=22, weight="bold")).pack(
                     anchor="w", pady=(0, 12))

    def _make_tree(self, parent, columns, widths):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="both", expand=True)
        tree = ttk.Treeview(frame, columns=columns, show="headings",
                            style="T.Treeview")
        for col, w in zip(columns, widths):
            tree.heading(col, text=col)
            tree.column(col, width=w, minwidth=50)
        sb = ctk.CTkScrollbar(frame, command=tree.yview)
        tree.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        tree.pack(side="left", fill="both", expand=True)
        return tree

    def _stat_card(self, parent, label, value, color):
        card = ctk.CTkFrame(parent, corner_radius=10)
        card.pack(side="left", expand=True, fill="x", padx=5)
        ctk.CTkLabel(card, text=str(value),
                     font=ctk.CTkFont(size=36, weight="bold"),
                     text_color=color).pack(pady=(18, 2))
        ctk.CTkLabel(card, text=label,
                     font=ctk.CTkFont(size=12),
                     text_color=C_DIM).pack(pady=(0, 18))

    def _selected_id(self, tree):
        sel = tree.selection()
        if not sel:
            messagebox.showwarning("Upozorenje", "Izaberite red iz liste.")
            return None
        return tree.item(sel[0])["values"][0]

    # ── Dashboard ─────────────────────────────────────────────────────────────

    def _view_dashboard(self):
        frame = ctk.CTkScrollableFrame(self.main, fg_color="transparent")
        frame.grid(row=0, column=0, sticky="nsew")
        self.current_frame = frame

        self._page_title(frame, "Dashboard")

        self.c.execute("SELECT COUNT(*) FROM Artikli WHERE Aktivan=1")
        ukupno = self.c.fetchone()[0]
        self.c.execute("SELECT COUNT(*) FROM Artikli WHERE Aktivan=1 AND Kolicina<=KriticnaKolicina")
        kriticnih = self.c.fetchone()[0]
        self.c.execute("SELECT COALESCE(SUM(Kolicina),0) FROM Artikli WHERE Aktivan=1")
        ukupno_kom = self.c.fetchone()[0]
        self.c.execute("SELECT COUNT(*) FROM Izdavanje")
        izd_count = self.c.fetchone()[0]

        stats = ctk.CTkFrame(frame, fg_color="transparent")
        stats.pack(fill="x", pady=(0, 10))
        self._stat_card(stats, "Artikala",        ukupno,      C_BLUE)
        self._stat_card(stats, "Komada na stanju", ukupno_kom, C_GREEN)
        self._stat_card(stats, "Kritičnih",        kriticnih,  C_RED if kriticnih else C_GREEN)
        self._stat_card(stats, "Izdavanja",         izd_count, C_ORANGE)

        if kriticnih:
            crit = ctk.CTkFrame(frame)
            crit.pack(fill="x", pady=5)
            ctk.CTkLabel(crit, text="Artikli ispod kritičnog nivoa",
                         font=ctk.CTkFont(size=14, weight="bold"),
                         text_color=C_RED).pack(anchor="w", padx=15, pady=(12, 6))
            t = self._make_tree(crit,
                ("Axapta", "Naziv", "Na stanju", "Kritična kol.", "Lokacija"),
                [110, 220, 100, 120, 140])
            self.c.execute("""SELECT Axapta, Naziv, Kolicina, KriticnaKolicina, Lokacija
                              FROM Artikli WHERE Aktivan=1 AND Kolicina<=KriticnaKolicina""")
            for row in self.c.fetchall():
                t.insert("", "end", values=[str(v or "-") for v in row], tags=("r",))
            t.tag_configure("r", foreground=C_RED)
            ctk.CTkFrame(crit, height=10, fg_color="transparent").pack()

        act = ctk.CTkFrame(frame)
        act.pack(fill="both", expand=True, pady=5)
        ctk.CTkLabel(act, text="Poslednja aktivnost",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(
                     anchor="w", padx=15, pady=(12, 6))
        t2 = self._make_tree(act, ("Artikal", "Količina", "Datum", "Tip"),
                             [240, 100, 130, 100])
        self.c.execute("""
            SELECT a.Naziv, i.Kolicina, i.DatumIzdavanja, 'Izdavanje'
            FROM Izdavanje i JOIN Artikli a ON a.ID=i.ArtikalID
            UNION ALL
            SELECT a.Naziv, p.Kolicina, p.DatumPrijema, 'Prijem'
            FROM Prijem p JOIN Artikli a ON a.ID=p.ArtikalID
            ORDER BY 3 DESC LIMIT 12
        """)
        for row in self.c.fetchall():
            tag = "p" if row[3] == "Prijem" else "i"
            t2.insert("", "end", values=[str(v or "-") for v in row], tags=(tag,))
        t2.tag_configure("p", foreground=C_GREEN)
        t2.tag_configure("i", foreground=C_ORANGE)
        ctk.CTkFrame(act, height=10, fg_color="transparent").pack()

    # ── Artikli ───────────────────────────────────────────────────────────────

    def _view_artikli(self):
        frame = ctk.CTkFrame(self.main, fg_color="transparent")
        frame.grid(row=0, column=0, sticky="nsew")
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=1)
        self.current_frame = frame

        # Toolbar
        bar = ctk.CTkFrame(frame, fg_color="transparent")
        bar.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        ctk.CTkLabel(bar, text="Artikli",
                     font=ctk.CTkFont(size=22, weight="bold")).pack(side="left")

        self._art_search = ctk.StringVar()
        entry = ctk.CTkEntry(bar, placeholder_text="Pretraga...",
                             width=200, textvariable=self._art_search)
        entry.pack(side="left", padx=(18, 5))
        self._art_search.trace("w", lambda *_: self._refresh_artikli())

        self._art_filter = ctk.StringVar(value="Svi")
        ctk.CTkOptionMenu(bar, values=["Svi", "Kritični", "U redu"],
                          variable=self._art_filter, width=110,
                          command=lambda _: self._refresh_artikli()).pack(side="left", padx=5)

        for text, cmd in [
            ("Ažuriraj kol.", self._dlg_azuriraj),
            ("Obriši",        self._dlg_obrisi),
            ("Izmeni",        self._dlg_izmeni),
            ("+ Dodaj",       self._dlg_dodaj),
        ]:
            ctk.CTkButton(bar, text=text, width=115,
                          command=cmd).pack(side="right", padx=3)

        # Table
        tbl = ctk.CTkFrame(frame)
        tbl.grid(row=1, column=0, sticky="nsew")
        cols = ("ID", "Axapta", "Naziv", "Količina", "Kritična kol.", "Lokacija", "Poslednje izd.")
        self.art_tree = self._make_tree(tbl, cols, [45, 100, 210, 95, 115, 120, 130])
        self._refresh_artikli()

    def _refresh_artikli(self):
        t = self.art_tree
        for i in t.get_children():
            t.delete(i)
        q = """SELECT ID, Axapta, Naziv, Kolicina, KriticnaKolicina, Lokacija, PoslednjeIzdavanje
               FROM Artikli WHERE Aktivan=1"""
        params = []
        s = self._art_search.get().strip()
        if s:
            q += " AND (Axapta LIKE ? OR Naziv LIKE ?)"
            params += [f"%{s}%", f"%{s}%"]
        f = self._art_filter.get()
        if f == "Kritični":
            q += " AND Kolicina<=KriticnaKolicina"
        elif f == "U redu":
            q += " AND Kolicina>KriticnaKolicina"
        self.c.execute(q, params)
        for row in self.c.fetchall():
            tag = "crit" if row[3] <= row[4] else ""
            t.insert("", "end", values=[str(v or "-") for v in row], tags=(tag,))
        t.tag_configure("crit", foreground=C_RED)

    def _dlg_dodaj(self):
        d = FormDialog(self, "Dodavanje novog artikla", [
            ("Axapta šifra",    "str", ""),
            ("Naziv",           "str", ""),
            ("Početna količina","int", "0"),
            ("Kritična količina","int","0"),
            ("Lokacija",        "str", ""),
        ])
        if d.result:
            ax, naz, kol, krit, lok = d.result
            self.c.execute("""INSERT INTO Artikli (Axapta,Naziv,Kolicina,KriticnaKolicina,Lokacija)
                              VALUES (?,?,?,?,?)""",
                           (ax, naz, int(kol), int(krit), lok or None))
            self.conn.commit()
            self._refresh_artikli()

    def _dlg_izmeni(self):
        aid = self._selected_id(self.art_tree)
        if not aid:
            return
        self.c.execute("SELECT Axapta,Naziv,KriticnaKolicina,Lokacija FROM Artikli WHERE ID=?", (aid,))
        a = self.c.fetchone()
        d = FormDialog(self, "Izmena artikla", [
            ("Axapta šifra",     "str", a[0] or ""),
            ("Naziv",            "str", a[1] or ""),
            ("Kritična količina","int", str(a[2])),
            ("Lokacija",         "str", a[3] or ""),
        ])
        if d.result:
            ax, naz, krit, lok = d.result
            self.c.execute("""UPDATE Artikli SET Axapta=?,Naziv=?,KriticnaKolicina=?,Lokacija=?
                              WHERE ID=?""", (ax, naz, int(krit), lok or None, aid))
            self.conn.commit()
            self._refresh_artikli()

    def _dlg_obrisi(self):
        aid = self._selected_id(self.art_tree)
        if not aid:
            return
        self.c.execute("SELECT Naziv FROM Artikli WHERE ID=?", (aid,))
        naziv = self.c.fetchone()[0]
        if messagebox.askyesno("Potvrda brisanja",
                               f"Arhivirati artikal '{naziv}'?\n(Istorija se čuva)"):
            self.c.execute("UPDATE Artikli SET Aktivan=0 WHERE ID=?", (aid,))
            self.conn.commit()
            self._refresh_artikli()

    def _dlg_azuriraj(self):
        aid = self._selected_id(self.art_tree)
        if not aid:
            return
        self.c.execute("SELECT Naziv,Kolicina FROM Artikli WHERE ID=?", (aid,))
        naziv, kol = self.c.fetchone()
        d = FormDialog(self, f"Ažuriranje količine – {naziv}", [
            (f"Nova količina  (trenutno: {kol})", "int", str(kol)),
        ])
        if d.result:
            self.c.execute("UPDATE Artikli SET Kolicina=? WHERE ID=?", (int(d.result[0]), aid))
            self.conn.commit()
            self._refresh_artikli()

    # ── Prijem ────────────────────────────────────────────────────────────────

    def _view_prijem(self):
        frame = ctk.CTkFrame(self.main, fg_color="transparent")
        frame.grid(row=0, column=0, sticky="nsew")
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=1)
        self.current_frame = frame

        bar = ctk.CTkFrame(frame, fg_color="transparent")
        bar.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        ctk.CTkLabel(bar, text="Prijem robe",
                     font=ctk.CTkFont(size=22, weight="bold")).pack(side="left")
        ctk.CTkButton(bar, text="+ Evidentiraj prijem",
                      command=self._dlg_prijem).pack(side="right")

        tbl = ctk.CTkFrame(frame)
        tbl.grid(row=1, column=0, sticky="nsew")
        cols = ("ID", "Artikal", "Axapta", "Količina", "Datum", "Napomena")
        self.prijem_tree = self._make_tree(tbl, cols, [45, 220, 100, 100, 120, 220])
        self._refresh_prijem()

    def _refresh_prijem(self):
        t = self.prijem_tree
        for i in t.get_children():
            t.delete(i)
        self.c.execute("""SELECT p.ID,a.Naziv,a.Axapta,p.Kolicina,p.DatumPrijema,p.Napomena
                          FROM Prijem p JOIN Artikli a ON a.ID=p.ArtikalID
                          ORDER BY p.DatumPrijema DESC""")
        for row in self.c.fetchall():
            t.insert("", "end", values=[str(v or "-") for v in row])

    def _dlg_prijem(self):
        self.c.execute("SELECT ID,Axapta,Naziv,Kolicina FROM Artikli WHERE Aktivan=1 ORDER BY Naziv")
        artikli = self.c.fetchall()
        if not artikli:
            messagebox.showwarning("Upozorenje", "Nema artikala u bazi.")
            return
        d = TransDialog(self, "Prijem robe", artikli, tip="prijem")
        if d.result:
            aid, kol, datum, napomena = d.result
            self.c.execute("UPDATE Artikli SET Kolicina=Kolicina+? WHERE ID=?", (kol, aid))
            self.c.execute("INSERT INTO Prijem(ArtikalID,Kolicina,DatumPrijema,Napomena) VALUES(?,?,?,?)",
                           (aid, kol, datum, napomena or None))
            self.conn.commit()
            self._refresh_prijem()
            messagebox.showinfo("Uspešno", f"Prijem evidentiran.\nPrimljeno: {kol} kom.")

    # ── Izdavanje ─────────────────────────────────────────────────────────────

    def _view_izdavanje(self):
        frame = ctk.CTkFrame(self.main, fg_color="transparent")
        frame.grid(row=0, column=0, sticky="nsew")
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=1)
        self.current_frame = frame

        bar = ctk.CTkFrame(frame, fg_color="transparent")
        bar.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        ctk.CTkLabel(bar, text="Izdavanje artikala",
                     font=ctk.CTkFont(size=22, weight="bold")).pack(side="left")
        ctk.CTkButton(bar, text="+ Evidentiraj izdavanje",
                      command=self._dlg_izdavanje).pack(side="right")

        tbl = ctk.CTkFrame(frame)
        tbl.grid(row=1, column=0, sticky="nsew")
        cols = ("ID", "Artikal", "Axapta", "Količina", "Datum", "Napomena")
        self.izd_tree = self._make_tree(tbl, cols, [45, 220, 100, 100, 120, 220])
        self._refresh_izdavanje()

    def _refresh_izdavanje(self):
        t = self.izd_tree
        for i in t.get_children():
            t.delete(i)
        self.c.execute("""SELECT i.ID,a.Naziv,a.Axapta,i.Kolicina,i.DatumIzdavanja,i.Napomena
                          FROM Izdavanje i JOIN Artikli a ON a.ID=i.ArtikalID
                          ORDER BY i.DatumIzdavanja DESC""")
        for row in self.c.fetchall():
            t.insert("", "end", values=[str(v or "-") for v in row])

    def _dlg_izdavanje(self):
        self.c.execute("""SELECT ID,Axapta,Naziv,Kolicina FROM Artikli
                          WHERE Aktivan=1 AND Kolicina>0 ORDER BY Naziv""")
        artikli = self.c.fetchall()
        if not artikli:
            messagebox.showwarning("Upozorenje", "Nema artikala sa dostupnom količinom.")
            return
        d = TransDialog(self, "Izdavanje artikla", artikli, tip="izdavanje")
        if d.result:
            aid, kol, datum, napomena = d.result
            self.c.execute("SELECT Kolicina,KriticnaKolicina FROM Artikli WHERE ID=?", (aid,))
            stara, krit = self.c.fetchone()
            if kol > stara:
                messagebox.showerror("Greška", f"Nema dovoljno na stanju. Dostupno: {stara} kom.")
                return
            nova = stara - kol
            self.c.execute("UPDATE Artikli SET Kolicina=?,PoslednjeIzdavanje=? WHERE ID=?",
                           (nova, datum, aid))
            self.c.execute("INSERT INTO Izdavanje(ArtikalID,Kolicina,DatumIzdavanja,Napomena) VALUES(?,?,?,?)",
                           (aid, kol, datum, napomena or None))
            self.conn.commit()
            self._refresh_izdavanje()
            msg = f"Izdato {kol} kom.\nNovo stanje: {nova} kom."
            if nova <= krit:
                msg += "\n\nUpozorenje: Dostignut kritičan nivo zaliha!"
            messagebox.showinfo("Uspešno", msg)

    # ── Istorija ──────────────────────────────────────────────────────────────

    def _view_istorija(self):
        frame = ctk.CTkFrame(self.main, fg_color="transparent")
        frame.grid(row=0, column=0, sticky="nsew")
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=1)
        self.current_frame = frame

        ctk.CTkLabel(frame, text="Istorija",
                     font=ctk.CTkFont(size=22, weight="bold")).grid(
                     row=0, column=0, sticky="w", pady=(0, 10))

        tabs = ctk.CTkTabview(frame)
        tabs.grid(row=1, column=0, sticky="nsew")

        cols = ("ID", "Artikal", "Axapta", "Količina", "Datum", "Napomena")
        widths = [45, 220, 100, 100, 130, 220]

        tab_i = tabs.add("  Izdavanje  ")
        t1 = self._make_tree(tab_i, cols, widths)
        self.c.execute("""SELECT i.ID,a.Naziv,a.Axapta,i.Kolicina,i.DatumIzdavanja,i.Napomena
                          FROM Izdavanje i JOIN Artikli a ON a.ID=i.ArtikalID
                          ORDER BY i.DatumIzdavanja DESC""")
        for row in self.c.fetchall():
            t1.insert("", "end", values=[str(v or "-") for v in row])

        tab_p = tabs.add("  Prijem  ")
        t2 = self._make_tree(tab_p, cols, widths)
        self.c.execute("""SELECT p.ID,a.Naziv,a.Axapta,p.Kolicina,p.DatumPrijema,p.Napomena
                          FROM Prijem p JOIN Artikli a ON a.ID=p.ArtikalID
                          ORDER BY p.DatumPrijema DESC""")
        for row in self.c.fetchall():
            t2.insert("", "end", values=[str(v or "-") for v in row])

    # ── Izvoz & Backup ────────────────────────────────────────────────────────

    def _view_izvoz(self):
        frame = ctk.CTkScrollableFrame(self.main, fg_color="transparent")
        frame.grid(row=0, column=0, sticky="nsew")
        self.current_frame = frame

        self._page_title(frame, "Izvoz & Backup")

        actions = [
            ("Izvoz u CSV",
             "Izvozi listu svih aktivnih artikala u CSV format (separator: ;).",
             self._export_csv),
            ("Izvoz u PDF",
             "Izvozi kompletnu listu artikala u PDF dokument.",
             lambda: self._export_pdf(False)),
            ("Izvoz kritičnih u PDF",
             "Izvozi samo artikle čija je količina ispod kritičnog nivoa.",
             lambda: self._export_pdf(True)),
            ("Backup baze podataka",
             "Pravi kopiju fajla artikli.db sa datumom i vremenom u nazivu.",
             self._backup),
        ]

        for title, desc, cmd in actions:
            card = ctk.CTkFrame(frame, corner_radius=10)
            card.pack(fill="x", pady=6)
            inner = ctk.CTkFrame(card, fg_color="transparent")
            inner.pack(fill="x", padx=18, pady=16)
            ctk.CTkLabel(inner, text=title,
                         font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w")
            ctk.CTkLabel(inner, text=desc, font=ctk.CTkFont(size=12),
                         text_color=C_DIM, wraplength=600, justify="left").pack(
                         anchor="w", pady=(4, 10))
            ctk.CTkButton(inner, text="Pokreni", width=120, command=cmd).pack(anchor="w")

    def _export_csv(self):
        self.c.execute("""SELECT ID,Axapta,Naziv,Kolicina,KriticnaKolicina,
                                 PoslednjeIzdavanje,Lokacija
                          FROM Artikli WHERE Aktivan=1""")
        rows = self.c.fetchall()
        if not rows:
            messagebox.showwarning("Upozorenje", "Nema artikala za izvoz.")
            return
        fname = f"lista_artikala_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        with open(fname, "w", encoding="utf-8") as f:
            f.write("ID;Axapta;Naziv;Količina;Kritična Količina;Poslednje Izdavanje;Lokacija\n")
            for row in rows:
                f.write(";".join([str(v or "") for v in row]) + "\n")
        messagebox.showinfo("Uspešno", f"Izvezeno u:\n{fname}")

    def _export_pdf(self, samo_kriticni):
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.pdfgen import canvas as pdfcanvas
        except ImportError:
            messagebox.showerror("Greška",
                "reportlab nije instaliran.\nPokrenite: pip install reportlab")
            return
        if samo_kriticni:
            self.c.execute("""SELECT ID,Axapta,Naziv,Kolicina,KriticnaKolicina,
                                     PoslednjeIzdavanje,Lokacija
                              FROM Artikli WHERE Aktivan=1 AND Kolicina<=KriticnaKolicina""")
            fname = f"kriticni_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        else:
            self.c.execute("""SELECT ID,Axapta,Naziv,Kolicina,KriticnaKolicina,
                                     PoslednjeIzdavanje,Lokacija
                              FROM Artikli WHERE Aktivan=1""")
            fname = f"artikli_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        rows = self.c.fetchall()
        if not rows:
            messagebox.showwarning("Upozorenje", "Nema podataka za izvoz.")
            return
        pdf = pdfcanvas.Canvas(fname, pagesize=letter)
        heads = ["ID", "Axapta", "Naziv", "Količina", "Krit.Kol.", "Posl.Izd.", "Lokacija"]
        y = 750
        for i, h in enumerate(heads):
            pdf.drawString(50 + i * 78, y, h)
        y -= 20
        for row in rows:
            for i, v in enumerate(row):
                pdf.drawString(50 + i * 78, y, str(v or ""))
            y -= 20
            if y < 50:
                pdf.showPage()
                y = 750
        pdf.save()
        messagebox.showinfo("Uspešno", f"PDF sačuvan kao:\n{fname}")

    def _backup(self):
        fname = f"artikli_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        try:
            shutil.copy2(DB_PATH, fname)
            messagebox.showinfo("Uspešno", f"Backup sačuvan kao:\n{fname}")
        except Exception as e:
            messagebox.showerror("Greška", f"Greška pri backup-u:\n{e}")


# ─── DIALOGS ──────────────────────────────────────────────────────────────────

class FormDialog(ctk.CTkToplevel):
    """Generic form dialog for simple key-value input."""

    def __init__(self, parent, title, fields):
        super().__init__(parent)
        self.title(title)
        self.resizable(False, False)
        self.grab_set()
        self.result = None

        ctk.CTkLabel(self, text=title,
                     font=ctk.CTkFont(size=16, weight="bold")).pack(
                     padx=28, pady=(22, 14), anchor="w")

        self._entries = []
        for label, ftype, default in fields:
            row = ctk.CTkFrame(self, fg_color="transparent")
            row.pack(fill="x", padx=28, pady=4)
            ctk.CTkLabel(row, text=label, width=210, anchor="w").pack(side="left")
            e = ctk.CTkEntry(row, width=230)
            e.insert(0, default)
            e.pack(side="left", padx=(8, 0))
            self._entries.append((ftype, e))

        btn = ctk.CTkFrame(self, fg_color="transparent")
        btn.pack(fill="x", padx=28, pady=(18, 22))
        ctk.CTkButton(btn, text="Potvrdi", command=self._submit).pack(side="right", padx=(6, 0))
        ctk.CTkButton(btn, text="Odustani", fg_color="transparent",
                      border_width=1, command=self.destroy).pack(side="right")
        self.wait_window()

    def _submit(self):
        vals = []
        for ftype, e in self._entries:
            v = e.get().strip()
            if ftype == "int":
                try:
                    int(v)
                except ValueError:
                    messagebox.showerror("Greška", "Unesite validan ceo broj.", parent=self)
                    return
            vals.append(v)
        self.result = vals
        self.destroy()


class TransDialog(ctk.CTkToplevel):
    """Dialog for prijem / izdavanje — article selector + quantity + date + note."""

    def __init__(self, parent, title, artikli, tip):
        super().__init__(parent)
        self.title(title)
        self.resizable(False, False)
        self.grab_set()
        self.result = None
        self._artikli = artikli

        ctk.CTkLabel(self, text=title,
                     font=ctk.CTkFont(size=16, weight="bold")).pack(
                     padx=28, pady=(22, 14), anchor="w")

        def row_frame():
            f = ctk.CTkFrame(self, fg_color="transparent")
            f.pack(fill="x", padx=28, pady=5)
            return f

        # Article
        r = row_frame()
        ctk.CTkLabel(r, text="Artikal:", width=150, anchor="w").pack(side="left")
        choices = [f"[{a[0]}] {a[1]} – {a[2]}  (stanje: {a[3]})" for a in artikli]
        self._art_var = ctk.StringVar(value=choices[0])
        ctk.CTkOptionMenu(r, values=choices,
                          variable=self._art_var, width=340).pack(side="left", padx=(8, 0))

        # Quantity
        r2 = row_frame()
        lbl = "Primljeno (kom):" if tip == "prijem" else "Izdato (kom):"
        ctk.CTkLabel(r2, text=lbl, width=150, anchor="w").pack(side="left")
        self._kol = ctk.CTkEntry(r2, width=340)
        self._kol.pack(side="left", padx=(8, 0))

        # Date
        r3 = row_frame()
        dlbl = "Datum prijema:" if tip == "prijem" else "Datum izdavanja:"
        ctk.CTkLabel(r3, text=dlbl, width=150, anchor="w").pack(side="left")
        self._dat = ctk.CTkEntry(r3, width=340)
        self._dat.insert(0, datetime.now().strftime("%d.%m.%Y"))
        self._dat.pack(side="left", padx=(8, 0))

        # Note
        r4 = row_frame()
        ctk.CTkLabel(r4, text="Napomena:", width=150, anchor="w").pack(side="left")
        self._nap = ctk.CTkEntry(r4, width=340)
        self._nap.pack(side="left", padx=(8, 0))

        btn = ctk.CTkFrame(self, fg_color="transparent")
        btn.pack(fill="x", padx=28, pady=(18, 22))
        ctk.CTkButton(btn, text="Potvrdi", command=self._submit).pack(side="right", padx=(6, 0))
        ctk.CTkButton(btn, text="Odustani", fg_color="transparent",
                      border_width=1, command=self.destroy).pack(side="right")
        self.wait_window()

    def _submit(self):
        sel = self._art_var.get()
        aid = int(sel.split("]")[0][1:])
        try:
            kol = int(self._kol.get().strip())
            if kol <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Greška", "Unesite pozitivan ceo broj za količinu.", parent=self)
            return
        self.result = (aid, kol, self._dat.get().strip(), self._nap.get().strip())
        self.destroy()


if __name__ == "__main__":
    app = App()
    app.mainloop()
