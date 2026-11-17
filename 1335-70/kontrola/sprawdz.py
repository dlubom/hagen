"""Porównanie niewyrównanych pozycji Survex z dwoma arkuszami i obliczeniami z października."""

import csv
import math
from pathlib import Path
import re
import subprocess
import tempfile


KONTROLA = Path(__file__).resolve().parent


def pozycje(svx, folder, nazwa):
    model = folder / f"{nazwa}.3d"
    subprocess.run(["cavern", "-w", "-qq", "-s", "-o", model, svx], check=True)
    zapis = subprocess.check_output(["dump3d", model], text=True)
    punkty = {}
    for wiersz in zapis.splitlines():
        pola = wiersz.split()
        if pola[:1] == ["NODE"]:
            nazwa_stacji = pola[4].strip("[]").removeprefix("kgw.")
            punkty[nazwa_stacji] = tuple(map(float, pola[1:4]))
    return punkty


def porownaj():
    with tempfile.TemporaryDirectory() as katalog:
        folder = Path(katalog)
        oryginal = (KONTROLA.parent / "pomiary.svx").read_text(encoding="utf-8")
        # W arkuszu 24 ma dwie pozycje. Rozdzielamy je tylko w kopii kontrolnej.
        zapis, ile = re.subn(r"(?m)^([ \t]*29[ \t]+)24(?=[ \t])", r"\g<1>24_return", oryginal)
        if ile != 1:
            raise ValueError("Kopia kontrolna wymaga jednego wiersza 29 → 24.")
        kopia = folder / "przed-wyrownaniem.svx"
        kopia.write_text("*fix kgw.i 0 0 0\n" + zapis, encoding="utf-8")
        punkty = pozycje(kopia, folder, "glowny")
        punkty.update(pozycje(KONTROLA.parent / "lokalny.svx", folder, "lokalny"))

    grupy = {"lipiec": [], "lokalny": [], "październik": []}
    with (KONTROLA / "wspolrzedne-archiwalne.tsv").open(encoding="utf-8") as tabela:
        for wiersz in csv.DictReader(tabela, delimiter="\t"):
            nazwa = wiersz["stacja"]
            pozycja = tuple(float(wiersz[k]) for k in ("Y_wschod_m", "X_polnoc_m", "H_m"))
            grupa = "lipiec"
            if nazwa.startswith("local."):
                grupa = "lokalny"
            elif nazwa.startswith("oct."):
                grupa = "październik"
            grupy[grupa].append((math.dist(pozycja, punkty[nazwa]), nazwa))

    print("Porównanie 3D po zaokrągleniu współrzędnych Survex do 0,01 m")
    for nazwa, roznice in grupy.items():
        blad, stacja = max(roznice)
        print(f"{nazwa:12} {len(roznice):3} pozycji, maks. {blad:.3f} m ({stacja})")
    luka = math.dist(punkty["24"], punkty["24_return"])
    print(f"Odległość między dwoma dojściami do 24 przed wyrównaniem: {luka:.2f} m")


if __name__ == "__main__":
    porownaj()
