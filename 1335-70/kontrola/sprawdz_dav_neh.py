"""Kontrola DAV ↔ NEH przed wyrównaniem. Uruchom bez opcji lub z --zapisz, aby odświeżyć TSV."""

import argparse
import csv
import io
import math
from pathlib import Path

KONTROLA = Path(__file__).resolve().parent
DAV = "dav-neh.tsv"
PAZ = "pazdziernik-obliczenia.tsv"
NAGLOWEK = (
    "od do jednostka D_m A V dN_DAV_m dE_DAV_m dH_DAV_m "
    "dN_z_arkuszy_m dE_z_arkuszy_m dH_z_arkuszy_m D_z_NEH_m A_z_NEH V_z_NEH "
    "N_DAV_m E_DAV_m H_DAV_m N_arkusz_m E_arkusz_m H_arkusz_m blad_wektora_m blad_pozycji_m"
).split()


def wczytaj(nazwa):
    with (KONTROLA / nazwa).open(encoding="utf-8", newline="") as plik:
        return list(csv.DictReader(plik, delimiter="\t"))


def odczyty():
    """Oba archiwalne pliki mają *data normal from to tape clino compass."""
    pomiary = {}
    for plik in ("pomiary.svx", "lokalny-pomiary.svx"):
        bloki = [("", None, False)]
        for linia in (KONTROLA.parent / plik).read_text(encoding="utf-8").splitlines():
            pola = linia.partition(";")[0].split()
            if not pola:
                continue
            nazwa, obrot, format_danych = bloki[-1]
            if pola[0] == "*begin":
                blok = pola[1] if len(pola) == 2 else ""
                prefiks = nazwa + blok + "." if blok and blok != "kgw" else nazwa
                bloki.append((prefiks, obrot, format_danych))
            elif pola[0] == "*end":
                bloki.pop()
            elif pola[:3] == ["*units", "compass", "clino"]:
                bloki[-1] = (nazwa, {"grads": 400, "degrees": 360}[pola[3]], format_danych)
            elif pola[0] == "*data":
                bloki[-1] = (nazwa, obrot, pola[1:] == "normal from to tape clino compass".split())
            elif not pola[0].startswith("*"):
                if obrot is None or not format_danych:
                    raise ValueError(f"{plik}: nierozpoznany format pomiaru {linia!r}")
                od, do, d, v, a = pola
                od, do = nazwa + od, nazwa + do
                if (od, do) == ("29", "24"):
                    do = "24_return"  # drugie dojście, przed wyrównaniem
                if do in pomiary:
                    raise ValueError(f"Powtórzony cel {do} w {plik}")
                pomiary[do] = (
                    od,
                    float(d),
                    None if a == "-" else float(a),
                    -obrot / 4 if v == "DOWN" else float(v),
                    obrot,
                )
    return pomiary


def formatuj(x, miejsca=4):
    return "" if x is None else f"{x:.{miejsca}f}"


def oblicz():
    arch = {
        r["stacja"]: tuple(float(r[k]) for k in ("X_polnoc_m", "Y_wschod_m", "H_m"))
        for r in wczytaj("wspolrzedne-archiwalne.tsv")
    }
    paz = wczytaj(PAZ)
    rubryki = {r["do"]: r for r in paz}
    pomiary = odczyty()
    if set(rubryki) != {s for s in pomiary if s.startswith("oct.")} or len(rubryki) != len(paz):
        raise ValueError("Wiersze październikowego formularza nie odpowiadają celowym w SVX.")
    pozycje = {"i": (0.0, 0.0, 0.0), "local.0": (0.0, 0.0, 0.0)}
    tabela = [NAGLOWEK]

    def celowa(do):
        if do in pozycje:
            return
        od, d, a, v, obrot = pomiary[do]
        celowa(od)  # w SVX odcinek od 65 zapisano po pomiarach od oct.6
        rad = math.tau / obrot
        rzut = d * math.cos(v * rad)
        if a is None:
            if abs(v) != obrot / 4:
                raise ValueError(f"Brak azymutu poza pionem {od} → {do}")
            wektor = (0.0, 0.0, math.copysign(d, v))
        else:
            wektor = (rzut * math.cos(a * rad), rzut * math.sin(a * rad), d * math.sin(v * rad))
        pozycja = pozycje[do] = tuple(x + y for x, y in zip(pozycje[od], wektor))

        if do in rubryki:
            r = rubryki[do]
            kat = float(r["R_azymut"])
            if (od, d, a % obrot, v, obrot) != (
                r["od"],
                float(r["L_m"]),
                kat % obrot,
                float(r["N_nachylenie"]),
                360,
            ):
                raise ValueError(f"Odczyty SVX inne niż na formularzu: {od} → {do}")
            a = kat  # na formularzu 373°, w SVX równoważne 13°
            if round(rzut, 3) != float(r["D_pozioma_arkusz_m"]):
                raise ValueError(f"Rzut poziomy DAV różni się od formularza w {od} → {do}")
            r["D_pozioma_obl_m"] = formatuj(rzut)
            for j, os in enumerate("NEH"):
                przyrost_arkusza = float(r[f"d{os}_arkusz_m"])
                if round(wektor[j], 2) != przyrost_arkusza:
                    raise ValueError(f"Przyrost {os} z DAV różni się od formularza w {od} → {do}")
                r[f"d{os}_obl_m"] = formatuj(wektor[j])
                r[f"{os}_arkusz_m"] = formatuj(arch[do][j], 2)
                r[f"{os}_suma_m"] = formatuj(arch[od][j] + przyrost_arkusza, 2)
                if r[f"{os}_arkusz_m"] != r[f"{os}_suma_m"]:
                    print(f"{do}, {os}: w arkuszu {arch[do][j]:.2f} m, suma rubryk {r[f'{os}_suma_m']} m")

        puste = (None,) * 3
        poz_arch = arch.get(do, puste)
        blad_p = math.dist(pozycja, poz_arch) if do in arch else None
        przyrost = odwrotne = puste
        blad_w = None
        if od in arch and do in arch:
            n, e, h = przyrost = tuple(y - x for y, x in zip(poz_arch, arch[od]))
            poziom = math.hypot(n, e)
            odwrotne = (
                math.hypot(poziom, h),
                math.atan2(e, n) % math.tau / rad if poziom else None,
                math.atan2(h, poziom) / rad,
            )
            blad_w = math.dist(wektor, przyrost)
        tabela.append(
            [
                od,
                do,
                "gon" if obrot == 400 else "°",
                formatuj(d, 2),
                formatuj(a, 0),
                formatuj(v, 0),
                *(formatuj(x) for x in wektor),
                *(formatuj(x, 2) for x in przyrost),
                *(formatuj(x) for x in odwrotne),
                *(formatuj(x) for x in pozycja),
                *(formatuj(x, 2) for x in poz_arch),
                formatuj(blad_w),
                formatuj(blad_p),
            ]
        )

    for stacja in pomiary:
        celowa(stacja)
    wektor_dav = tuple(x - y for x, y in zip(pozycje["13"], pozycje["11"]))
    wektor_neh = tuple(x - y for x, y in zip(arch["13"], arch["11"]))
    print(f"11 → 12 → 13: różnica całego wektora {math.dist(wektor_dav, wektor_neh):.4f} m")
    if set(arch) - pozycje.keys():
        raise ValueError(f"Poza obliczonym ciągiem: {set(arch) - pozycje.keys()}")
    return {DAV: tabela, PAZ: [list(paz[0]), *(list(r.values()) for r in paz)]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--zapisz", action="store_true", help="zapisz ponownie przeliczone tabele")
    opcje = parser.parse_args()
    for nazwa, wiersze in oblicz().items():
        tekst = io.StringIO()
        csv.writer(tekst, delimiter="\t", lineterminator="\n").writerows(wiersze)
        oczekiwany = tekst.getvalue().encode("utf-8")
        plik = KONTROLA / nazwa
        if opcje.zapisz:
            plik.write_bytes(oczekiwany)
        elif plik.read_bytes() != oczekiwany:
            raise SystemExit(f"{nazwa}: wynik różni się od TSV. Porównaj dane źródłowe i wersję z --zapisz.")
        print(f"{nazwa}: {len(wiersze) - 1} wierszy")


if __name__ == "__main__":
    main()
