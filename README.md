# Hagengebirge · Kälbergruben-Windloch (1335/70)

[Model 3D z terenem](https://dlubom.github.io/hagen/#model) · [Mapa 2D z GPS i planami](https://dlubom.github.io/hagen/#mapa)

[Mapa HTML masywu do pracy offline](mapa/index.html) · [Ciąg 49,45 m na planie](1335-70/kontrola/lokalny-na-planie.html) · [Höhlenbuch po polsku](1335-70/zrodla/hoehlenbuch/tlumaczenie-pl.md)

[Audyt kart, jednostek i brakującego dowiązania](1335-70/kontrola/audyt-pomiarow.md) · [Model do otwarcia w Aven](hagen.3d) · [Poligon na planie archiwalnym](1335-70/kontrola/porownanie-planu.jpg) · [Profil W–E](1335-70/kontrola/profil-we.svg) · [16 wybranych przekrojów z dziennika](1335-70/kontrola/przekroje-polowe.jpg)

Główny model ma **112 stacji** i obejmuje wszystkie 111 odcinków z kart. Zmierzono **98 odcinków podziemnych o łącznej długości 1037,55 m** oraz 13 powierzchniowych o długości 198,80 m. Rozpiętość pionowa części podziemnej wynosi 71,59 m, od E2 do stacji 79.

Na mapie i w 3D widać siedem celowych z karty 1 (49,45 m) przy południowej ścianie Große Halle. Przerywana linia **`kgw.2 → local.4`** to sztuczny łącznik **do weryfikacji w terenie**. Jego rzut 12,71 m wyznaczono z planu, a różnicę wysokości umownie przyjęto równą zeru. Survex wyłącza ten bok z długości jaskini. [Dopasowanie i wskazówki terenowe](1335-70/kontrola/dowiazanie.md) · [Karta 1 w pierwotnym układzie lokalnym](1335-70/lokalny.3d)

Plan pokazuje także korytarze poza zasięgiem tych kart. Opis obu otworów w GPX podaje 1235 m długości i 77 m głębokości. Te dwie liczby odtwarzają się po zaokrągleniu ręcznych sum kart (1235,25 m) i rozpiętości dawnych rzędnych (76,77 m), w obu przypadkach z powierzchnią. Pochodzenie wartości w GPX pozostaje nieudokumentowane. W książce wydanej w 1979 r. dla poznanej wówczas części podano 270 m i 40 m.

## Pliki i kompilacja

Plik wejściowy masywu [hagen.svx](hagen.svx) zawiera georeferencję. [Pomiary jaskini](1335-70/pomiary.svx) są ułożone według kart i zachowują kierunki celowania. Katalog [zrodla](1335-70/zrodla/) zawiera dwanaście otrzymanych fotografii zapisanych pod czytelnymi nazwami. Są wśród nich plan, karty 1–7, dwa arkusze współrzędnych oraz szkic i obliczenia dodatkowego ciągu od stacji 65. Osobno zarchiwizowano [cztery fotografie stron 303–306 Höhlenbuch wraz z polskim przekładem](1335-70/zrodla/hoehlenbuch/).

```sh
cavern -w -o hagen.3d hagen.svx
cavern -w -s -o 1335-70/lokalny.3d 1335-70/lokalny.svx
aven hagen.3d
```

Sprawdzono w Survex 1.4.24. W Aven włączenie odcinków powierzchniowych pokazuje ciąg między otworami. Pomiary poprzeczne są w [tabeli wymiarów](1335-70/wymiary.tsv), w kolejności pól formularza ← ↑ ↓ →, przy konkretnych wierszach. Karta powierzchniowa i dodatek od stacji 65 mają puste rubryki wymiarów. Puste pole, zero, znak zapytania i opis terenowy mają różne znaczenia. Porównanie podpisanych przekrojów 52, 71 i 72 przemawia za odczytem wymiarów przy stacji docelowej. Dla ciągu lokalnego jest to założenie przez analogię. [Przekroje i profil lokalny](1335-70/kontrola/przekroje-a-ciag-lokalny.jpg). Numery stacji na [planszy przekrojów](1335-70/kontrola/przekroje-polowe.jpg) pochodzą z podpisów przy szkicach.

## Otwory

Przyjęto WGS84 dla podanych długości i szerokości geograficznych. Wysokości zachowano w podanych metrach. Wynikowy układ poziomy to WGS84 / UTM 33N (EPSG:32633). Survex uwzględnia historyczną deklinację obliczoną dla miejsca i dat pomiarów oraz zbieżność południków.

| Otwór | Stacja | Długość E | Szerokość N | Podana wysokość | Wysokość w modelu |
|---|---|---:|---:|---:|---:|
| Dolny, Unterer Eingang | E na karcie 2, `kgw.e1` | 13,13852° | 47,518112° | 1661 m | 1661,00 m |
| Górny, Einstieg Dohlenschacht | XIII na karcie 2, `kgw.e2` | 13,13725° | 47,518052° | 1729 m | 1724,04 m |

Punktem stałym jest dolny otwór. Górny pozostaje kontrolą zewnętrzną. Od dolnego otworu ciąg powierzchniowy daje przewyższenie **63,04 m**, a podane wysokości dają **68,00 m**. Model wyznacza górny otwór w 13,137261° E, 47,518084° N, około **3,70 m** od podanej pozycji w poziomie i **4,96 m niżej**. Na planie archiwalnym otwory opisano jako 1680 i 1743 m. W obliczeniach polowych punkt I, kopczyk przed wejściem, ma dopisek 1690 m. Do kontroli archiwalnej jego rzędną lokalną przyjęto jako zero.

## Mapa masywu i jaskini

Na [GitHub Pages](https://dlubom.github.io/hagen/) zakładka **Model 3D** pokazuje poligon Kälbergruben-Windloch w CaveView na tle terenu z austriackiego skanowania laserowego BEV. W panelu **Warstwy modelu** przycisk **Zbliż do łącznika** ustawia widok na bok między `kgw.2` i `local.4`. Można też zmieniać krycie terenu i przełączać poszczególne warstwy.

Zakładka **LiDAR** pokazuje punkty gruntu SAGIS w kolorach ortofotomapy basemap.at. Widoki **Nad terenem** i **Pod terenem** pozwalają porównać powierzchnię z poligonem. Kafel obejmuje oba otwory i rzut całego poligonu Kälbergruben-Windloch. Potree-Next wymaga przeglądarki z WebGPU. [Źródła i kontrola chmury](1335-70/kontrola/lidar.md)

W zakładce **Mapa 2D** wybór planu przenosi widok do jaskini. Kliknięcie przerywanego łącznika pokazuje jego końce, długość i założenie wysokości. Dostępne są plan 1:500 i rycina z 1963 r. dla Kälbergruben-Windloch oraz rzut Tantalhöhle (1335/30) narysowany przez W. Waagnera w 1979 r. Rzut Tantalhöhle dowiązano do punktu GPX `Tantalhohle_30` przy otworze opisanym na planie jako 1710 m. Skalę wyznacza drukowana siatka 500 m, a orientację kierunek od otworu do dawnego punktu 302 w Riesenhalle. W niezależnym punkcie kontrolnym 231 przy Seufzertreppe różnica wynosi 49 m. [Georeferencja Tantalhöhle i identyfikacja obu punktów](1335-30/georeferencja.md)

W menu **Podkład** można wybrać mapę z poziomicami, cieniowaną **Rzeźbę terenu** z basemap.at, ortofotomapę lub geologię GeoSphere Austria 1:50 000. **Uskoki geologiczne** można włączyć na dowolnym tle. Po wybraniu **Odczyt skały** kliknij punkt na mapie, aby zobaczyć opis jednostki geologicznej na powierzchni i numer pozycji w legendzie. [Źródła podkładów](mapa/podklady-2d.md)

Podkłady archiwalne to **Ortofotomapa SAGIS 1952–1954** oraz **Historyczna mapa geologiczna 1:28 800** z arkuszami GeoSphere z lat 1846–1898. Odczyt skały korzysta ze współczesnej geologii także na podkładach archiwalnych.

Lista **Ciągi jaskiń z h2026** przybliża wybraną jaskinię. Warstwa zawiera 9724 podziemne odcinki dla 60 obiektów. Kliknięcie ciągu pokazuje nazwę i liczbę odcinków. Aby odświeżyć warstwę z lokalnej kopii gałęzi `h2026`, uruchom `python3 scripts/import_h2026.py /ścieżka/do/test2`. [Źródłowy projekt Survex](https://github.com/dlubom/test2/tree/ec21231914280347e05cedd10d9e9aff55955d89)

GitHub Actions po zmianie na `main` kompiluje `hagen.svx`, generuje warstwy mapy z tego samego modelu, GPX i fotografii planów oraz publikuje całość. Do lokalnego podglądu potrzebne są Survex 1.4.24, PROJ (`cs2cs`), Python z NumPy i OpenCV oraz `curl` do pobrania CaveView.

```sh
python3 scripts/build_pages.py
python3 scripts/serve_pages.py
```

Podgląd atlasu działa pod `http://127.0.0.1:8000/#lidar`. Skrypt serwera obsługuje odczyt fragmentów plików binarnych przez Potree.

[Mapa HTML do pracy offline](mapa/index.html) zawiera cieniowaną rzeźbę terenu z poziomicami, wszystkie 1063 punkty GPX, główny poligon Survex i ciągi jaskiń z h2026. Znaczniki otworów Kälbergruben-Windloch pozwalają porównać podane współrzędne, rekordy GPX i wynik kompilacji.

W GPX dolny otwór `Kalbergrube_70-d` leży 2,6 m od podanej pozycji i ma wysokość 1662 m. Górny `Kalbergrube_70-g` leży 1,8 m od podanej pozycji i ma wysokość 1733 m. Po zmianie danych wejściowych mapę offline można odświeżyć poleceniem `python3 mapa/odswiez.py` (wymaga `dump3d` i `cs2cs`). [GPX z punktami](mapa/zrodla/Hagengebirge-2025-8.gpx)

## Kontrola digitalizacji

- **Plan 1:500.** Na fotografii planu archiwum Landesverein für Höhlenkunde in Salzburg są daty pomiarów 1.07.1963 i 20.07.1985. Poligon po wyrównaniu naniesiono w lokalnym układzie Waagnera, korzystając z przecięć drukowanej siatki 50 m. Zgadza się przebieg od górnego otworu przez centralne partie, oba zachodnie ramiona do stacji 51 i 65 oraz odnoga w kierunku *Versturzzone*. W starej części (*Alter Teil*) widoczne są również odcinki bez odpowiedników w kartach. Fałdy papieru i perspektywa zdjęcia ograniczają dokładność nakładki. [Porównanie](1335-70/kontrola/porownanie-planu.jpg)
- **Jednostki.** W lipcowych wierszach kart z 20.07.1985 zarówno azymut, jak i nachylenie są w gradach. W odgałęzieniu od stacji 65 archiwalny rachunek odtwarza się w stopniach. Odcinek 4–2 ma zapis 373, równoważny 13° w tym rachunku. Ukośne kreski na polach stopniowych formularza i brak kresek na gradowych pozostawiają wątpliwość co do jednostki terenowej. W wariancie stopniowym odnoga dochodzi do strefy zawaliska narysowanej na planie. Przyjęcie gradów dla całego odgałęzienia przesuwa punkt `oct.1` o 14,57 m w rzucie. Datę 8.10.1985 przyjęto z podpisanego szkicu i arkusza obliczeń. Sam dzień pomiaru terenowego pozostaje niepotwierdzony. [Arkusz obliczeń](1335-70/zrodla/1985-10-obliczenia.jpg)
- **Współrzędne.** Obliczono od nowa położenia przed wyrównaniem i porównano ze 112 wpisami archiwalnymi. W 98 pozycjach głównego ciągu lipcowego największa różnica 3D wynosi 1,4 cm, w 8 lokalnych 0,8 cm, a w 6 dodatkowych 2,9 cm. Największa różnica dodatku wypada przy stacji 5, gdzie zapisane 11,52 m i −2,57 m dają 8,95 m, a w arkuszu wpisano 8,99 m. Stacja 12 jest poza kadrem tabeli. Łączny wektor 11–12–13 zgadza się z pozycjami stacji 11 i 13 do 0,9 cm. Te wartości mierzą zgodność odczytu i rachunku z archiwum. [Transkrypcja współrzędnych](1335-70/kontrola/wspolrzedne-archiwalne.tsv)
- **Pętla.** Dwa dojścia od 19 do 24 dają przed wyrównaniem różnicę +0,51 m na wschód, +2,51 m na północ i −2,10 m w pionie. Błąd przestrzenny wynosi **3,31 m na 131,95 m (2,51%)** i jest widoczny już w archiwalnych obliczeniach. W modelu oba dojścia kończą się na jednej stacji 24. [Raport Survex](hagen.err)
- **Odczyty kart.** Na karcie 2 suma odcinków wynosi 198,80 m przy ręcznej sumie 198,70 m, a na karcie 7 wynosi 153,25 m przy zapisanych 152,25 m. W obu przypadkach wektory potwierdzają archiwalne współrzędne. Rozróżniono 66 i 66a, zachowano pion 80–81 oraz poprawiony na karcie początek odcinka 14–82. Numeracja październikowa ma osobny prefiks `oct`.
- **Ciąg lokalny z karty 1.** Na większej fotografii planu kształt i wymiary dwóch załamań przy południowej ścianie Große Halle odpowiadają odcinkom 2–3–4. Druga odnoga kończy się około 2,2 m od proponowanej pozycji A. Rozwidlenia należy szukać około 14,5 m w rzucie od głównej stacji 2, między podpisami *Dachsbau mit Belüftung* i *unterlagernde Eiskapelle*. Wysokość i wymiary przejścia pozostają do sprawdzenia. [Plansza i opis roboczego dowiązania](1335-70/kontrola/dowiazanie.md)

Porównanie wszystkich 111 celowych, w obu kierunkach DAV ↔ NEH, odtwarza `python3 1335-70/kontrola/sprawdz_dav_neh.py`. [Wyniki dla każdego boku](1335-70/kontrola/dav-neh.tsv) · [Rubryki formularza październikowego](1335-70/kontrola/pazdziernik-obliczenia.tsv)

Kontrolę względem archiwum można powtórzyć poleceniem `python3 1335-70/kontrola/sprawdz.py` (Python 3.9+, `cavern`, `dump3d`). Skrypt rozdziela dwa dojścia do 24 w kopii tymczasowej i porównuje pozycje zapisane w modelu z dokładnością do 0,01 m. Po zaokrągleniu współrzędnych maksymalne różnice wynoszą odpowiednio 1,7 cm, 1,4 cm i 3,3 cm. Do odtworzenia osi w układzie drukowanego planu służy [uklad-planu.svx](1335-70/kontrola/uklad-planu.svx).

## Niemieckojęzyczne źródła

- Austriacki kataster w *Die Höhle* (1964), s. 90, wymienia 1335/70 jako *Kälbergrubenwindloch*, na południe od Brunnalm, na wysokości 1680 m. [Wpis katastralny](https://www.zobodat.at/pdf/Hoehle_015_0089-0091.pdf#page=2)
- G. Schwarzenberger, *Kälbergrubenwindloch 1335/70*, „Atlantis” (1981), zeszyt 3/4, s. 11–12. Bibliografia potwierdza publikację planu. Egzemplarz zeszytu figuruje w katalogu CNDS. W publicznie dostępnych materiałach nie udało się odnaleźć skanu tych stron ani odrębnego historycznego przekroju podłużnego. Dołączony profil W–E przedstawia ciąg główny sprzed dowiązania karty 1. [Bibliografia, poz. 82.0396](https://www.ssslib.ch/bbs/download/BBS1-27%20scan/Bbs-21.pdf#page=23) · [Katalog zeszytu](https://catalogue.cnds.ffspeleo.fr/index.php?id=10653&lvl=bulletin_display)
- *Salzburger Höhlenbuch*, tom 3 (1979), s. 303–304. Hasło 1335/70 podaje także nazwę *Sturmloch* oraz historyczne parametry 270 m długości, 160 m rozciągłości poziomej i 40 m deniwelacji. Na s. 304 znajduje się plan F. Koppenwallnera z 1963 r. (ryc. 276). Strony 305–306 opisują inne jaskinie i rejon hal Angeralm i Fillingalm. [Strona 303](1335-70/zrodla/hoehlenbuch/s-303.jpg) · [Strona 304 z planem](1335-70/zrodla/hoehlenbuch/s-304.jpg) · [Pełny przekład czterech stron](1335-70/zrodla/hoehlenbuch/tlumaczenie-pl.md)
- Gottfried Tichy w objaśnieniach do arkusza geologicznego *94 Hallein* (1990), s. 67, zalicza Kälbergrubenwindloch do jaskiń lodowych południowego skraju masywu. [Geologische Bundesanstalt](https://opac.geologie.ac.at/ais312/dokumente/094_Hallein.pdf#page=68)
