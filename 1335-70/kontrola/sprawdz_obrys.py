"""Test położeń i szerokości ciągu z karty 1 na obrysie z lokalny-na-planie.html.

Wymaga NumPy i Pillow. Współrzędne obrazu dotyczą planu obróconego o 90° w lewo.
"""

import base64
import csv
import io
import json
from pathlib import Path
import re

import numpy as np
from PIL import Image


HTML = Path(__file__).with_name("lokalny-na-planie.html").read_text(encoding="utf-8")
DANE = json.loads(re.search(r'<script id="data" type="application/json">(.*?)</script>', HTML)[1])
PNG = base64.b64decode(re.search(r'raster.src="data:image/png;base64,([^"]+)', HTML)[1])
OBRYS = np.asarray(Image.open(io.BytesIO(PNG))) > 127
SIATKA = np.array(DANE["grid"])
LOKALNE = {st: np.array(xyz[:2]) for st, xyz in DANE["local"].items()}


def na_planie(en):
    """Interpolacja w prostokątach siatki 50 m, jak w nakładce HTML."""
    e, n = en.T
    u, v = (e + 350) / 50, (100 - n) / 50
    i = np.clip(np.floor(u).astype(int), 0, 6)
    j = np.clip(np.floor(v).astype(int), 0, 3)
    a, b = (u - i)[:, None], (v - j)[:, None]
    gorna = (1 - a) * SIATKA[j, i] + a * SIATKA[j, i + 1]
    dolna = (1 - a) * SIATKA[j + 1, i] + a * SIATKA[j + 1, i + 1]
    return (1 - b) * gorna + b * dolna


def wewnatrz(piksele):
    x, y = np.rint(piksele).astype(int).T
    x, y = x - 1010, y - 32
    wys, szer = OBRYS.shape
    w_kadrze = (x >= 0) & (x < szer) & (y >= 0) & (y < wys)
    return w_kadrze & OBRYS[y.clip(0, wys - 1), x.clip(0, szer - 1)]


def dlugosc_wewnatrz(poczatki, odcinki=DANE["edges"]):
    suma = np.zeros(len(poczatki))
    for od, do in odcinki:
        wektor = LOKALNE[do] - LOKALNE[od]
        dlugosc = np.linalg.norm(wektor)
        liczba = int(np.ceil(dlugosc / 0.16))
        for k in range(liczba):
            en = poczatki + LOKALNE[od] + wektor * ((k + 0.5) / liczba)
            suma += wewnatrz(na_planie(en)) * (dlugosc / liczba)
    return suma


def caly_przebieg(poczatki, odcinki):
    stacje = dict.fromkeys(st for para in odcinki for st in para)
    for st in stacje:
        poczatki = poczatki[wewnatrz(na_planie(poczatki + LOKALNE[st]))]
    dlugosc = sum(np.linalg.norm(LOKALNE[b] - LOKALNE[a]) for a, b in odcinki)
    wyniki = dlugosc_wewnatrz(poczatki, odcinki)
    return poczatki[np.isclose(wyniki, dlugosc, rtol=0, atol=1e-8)]


def szerokosc(poczatki, stacja, kierunek):
    """Pierwsze wyjście promienia z obrysu po lewej i prawej, krok 0,1 m."""
    poprzeczny = np.array([-kierunek[1], kierunek[0]]) / np.linalg.norm(kierunek)
    suma = np.zeros(len(poczatki))
    for strona in (1, -1):
        odleglosci = np.full(len(poczatki), np.nan)
        for krok in range(801):
            aktywne = np.flatnonzero(np.isnan(odleglosci))
            if not aktywne.size:
                break
            dystans = krok / 10
            en = poczatki[aktywne] + LOKALNE[stacja] + strona * dystans * poprzeczny
            trafienia = ~wewnatrz(na_planie(en))
            odleglosci[aktywne[trafienia]] = dystans
        if np.isnan(odleglosci).any():
            raise ValueError("Promień przekroczył zakres testu 80 m.")
        suma += odleglosci
    return suma


def porownaj():
    robocze = np.array([DANE["working"]])
    odcinki = DANE["edges"]
    w_obrysie = dlugosc_wewnatrz(robocze, odcinki)[0]
    wektor = robocze[0] + LOKALNE["4"] - DANE["main"]["k2"]
    print(f"Dowiązanie robocze kgw.2 → local.4: ΔE {wektor[0]:+.2f}, "
          f"ΔN {wektor[1]:+.2f} m, rzut {np.linalg.norm(wektor):.2f} m")
    print(f"Rzut ciągu lokalnego w obrysie: {w_obrysie:.2f} m")
    for od, do in (("0", "1"), ("1", "2")):
        wynik = szerokosc(robocze, do, LOKALNE[do] - LOKALNE[od])[0]
        print(f"Szerokość w roboczym położeniu stacji {do} dla {od}–{do}: {wynik:.1f} m")

    e, n = np.meshgrid(np.arange(-155, 20.25, 0.25), np.arange(-40, 130.25, 0.25))
    poczatki = np.column_stack((e.ravel(), n.ravel()))
    dlugosc = sum(np.linalg.norm(LOKALNE[b] - LOKALNE[a]) for a, b in DANE["edges"])
    for st in ("1", "2"):
        piksele = na_planie(poczatki + LOKALNE[st])
        x, y = piksele.T
        for nazwa, y_min, y_max in (("kanion", 140, 345), ("wylot", 345, 400)):
            zakres = (x > 1040) & (x < 1198) & (y >= y_min) & (y < y_max)
            kandydaci = poczatki[zakres & wewnatrz(piksele)]
            wyniki = dlugosc_wewnatrz(kandydaci)
            idx = np.argmax(wyniki)
            print(f"{nazwa}, stacja {st}: maks. {wyniki[idx]:.2f} m "
                  f"({wyniki[idx] / dlugosc:.1%}), początek E,N {kandydaci[idx]}")

    mozliwe = caly_przebieg(poczatki, DANE["edges"])
    print(f"Cały ciąg w odczytanym obrysie: {len(mozliwe)} położeń na siatce co 0,25 m")
    przy_odnodze = np.array([DANE["fork"]])
    for od, do in (("0", "1"), ("1", "2"), ("2", "3"), ("3", "4")):
        kierunek = LOKALNE[do] - LOKALNE[od]
        for st in (od, do):
            przy = szerokosc(przy_odnodze, st, kierunek)[0]
            minimum = min(szerokosc(mozliwe, st, kierunek))
            print(f"{od}–{do}, przekrój w {st}: odnoga {przy:.1f} m, minimum siatki {minimum:.1f} m")


def test_bez_galezi():
    """0–1–2–3–4 w obrysie, bez warunku dla wznoszącego się ramienia 2–C–B–A."""
    tabela = Path(__file__).resolve().parents[1] / "wymiary.tsv"
    with tabela.open(encoding="utf-8") as plik:
        wiersze = [w for w in csv.DictReader(plik, delimiter="\t")
                   if w["seria"] == "local" and w["lewo_m"] and w["prawo_m"]]
    odcinki = [(w["od"], w["do"]) for w in wiersze]
    teren = np.array([float(w["lewo_m"]) + float(w["prawo_m"]) for w in wiersze])
    for podzial in (4, 10):
        wschod = np.arange(-155 * podzial, 20 * podzial + 1) / podzial
        polnoc = np.arange(-40 * podzial, 130 * podzial + 1) / podzial
        mozliwe = []
        for pas in np.array_split(polnoc, 60):
            e, n = np.meshgrid(wschod, pas)
            poczatki = np.column_stack((e.ravel(), n.ravel()))
            mozliwe.append(caly_przebieg(poczatki, odcinki))
        mozliwe = np.vstack(mozliwe)
        szer = np.column_stack([szerokosc(mozliwe, b, LOKALNE[b] - LOKALNE[a]) for a, b in odcinki])
        blad = np.abs(szer - teren).max(axis=1)
        najlepszy = np.argmin(blad)
        print(f"Bez warunku dla C/B/A, krok {1 / podzial:.2f} m: {len(mozliwe)} położeń, "
              f"minimum szerokości w 2: {min(szer[:, odcinki.index(('1', '2'))]):.1f} m. "
              f"Najmniejsza największa różnica czterech szerokości: {blad[najlepszy]:.1f} m "
              f"(szerokości {szer[najlepszy]} m).")


if __name__ == "__main__":
    porownaj()
    test_bez_galezi()
