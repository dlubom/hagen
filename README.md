# Hagengebirge · Kälbergruben-Windloch (1335/70)

[Model 3D z terenem](https://dlubom.github.io/hagen/#model) · [Mapa 2D z GPS i planami](https://dlubom.github.io/hagen/#mapa)

[Mapa HTML masywu do pracy offline](mapa/index.html) · [Ciąg 49,45 m na planie](1335-70/kontrola/lokalny-na-planie.html) · [Höhlenbuch po polsku](1335-70/zrodla/hoehlenbuch/tlumaczenie-pl.md)

[Audyt kart, jednostek i brakującego dowiązania](1335-70/kontrola/audyt-pomiarow.md) · [Model do otwarcia w Aven](hagen.3d) · [Poligon na planie archiwalnym](1335-70/kontrola/porownanie-planu.jpg) · [Profil W–E](1335-70/kontrola/profil-we.svg) · [16 wybranych przekrojów z dziennika](1335-70/kontrola/przekroje-polowe.jpg)

Projekt obejmuje wszystkie odcinki z dostarczonych kart — łącznie 111. Główny model ma 104 stacje i obejmuje 91 odcinków podziemnych o łącznej długości **988,10 m** oraz 13 powierzchniowych o długości **198,80 m**. Podziemna część tego poligonu ma rozpiętość pionową **71,59 m**, od E2 do stacji 79. Kolejne 7 odcinków (49,45 m) należy do pomiaru w starych partiach o nieustalonym dowiązaniu. Mają [własny model lokalny](1335-70/lokalny.3d). Plan pokazuje także korytarze poza zasięgiem tych kart. Opis obu otworów w GPX podaje 1235 m długości i 77 m głębokości. Te dwie liczby odtwarzają się po zaokrągleniu ręcznych sum kart (1235,25 m) i rozpiętości dawnych rzędnych (76,77 m), w obu przypadkach z powierzchnią. Pochodzenie wartości w GPX pozostaje nieudokumentowane. W książce wydanej w 1979 r. dla poznanej wówczas części podano 270 m i 40 m.

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

Na [GitHub Pages](https://dlubom.github.io/hagen/) zakładka **Model 3D** pokazuje poligon Survex w CaveView na tle terenu z austriackiego skanowania laserowego BEV. Można zmieniać krycie terenu oraz przełączać odcinki podziemne i powierzchniowe. W zakładce **Mapa 2D** można nałożyć plan 1:500 lub rycinę z 1963 r. na mapę z poziomicami albo ortofotomapę. Kliknięcie otworu pokazuje podane współrzędne, rekord GPX i położenie obliczone przez Survex. Opis dopasowania znajduje się przy każdym planie.

GitHub Actions po zmianie na `main` kompiluje `hagen.svx`, generuje warstwy mapy z tego samego modelu, GPX i fotografii planów oraz publikuje całość. Do lokalnego podglądu potrzebne są Survex 1.4.24, PROJ (`cs2cs`), Python z NumPy i OpenCV oraz `curl` do pobrania CaveView.

```sh
python3 scripts/build_pages.py
python3 -m http.server --directory build/pages 8000
```

[Otwórz mapę HTML](mapa/index.html) w przeglądarce. Plik działa offline i zawiera cieniowaną rzeźbę terenu z poziomicami, wszystkie 1063 punkty i 11 śladów z GPX (2762 wierzchołki) oraz główny poligon Survex. Widok jaskini pokazuje otwory, przebieg pod ziemią i ciąg powierzchniowy. Znaczniki otworów pozwalają porównać współrzędne podane przez użytkownika, rekordy GPX i wynik kompilacji.

W GPX dolny otwór `Kalbergrube_70-d` leży 2,6 m od podanej pozycji i ma wysokość 1662 m. Górny `Kalbergrube_70-g` leży 1,8 m od podanej pozycji i ma wysokość 1733 m. Po zmianie GPX lub rekompilacji modelu dane mapy można odświeżyć poleceniem `python3 mapa/odswiez.py` (wymaga `dump3d` i `cs2cs`). [Oryginalny GPX](mapa/zrodla/Hagengebirge-2025-8.gpx)

## Kontrola digitalizacji

- **Plan 1:500.** Na fotografii planu archiwum Landesverein für Höhlenkunde in Salzburg są daty pomiarów 1.07.1963 i 20.07.1985. Poligon po wyrównaniu naniesiono w lokalnym układzie Waagnera, korzystając z przecięć drukowanej siatki 50 m. Zgadza się przebieg od górnego otworu przez centralne partie, oba zachodnie ramiona do stacji 51 i 65 oraz odnoga w kierunku *Versturzzone*. W starej części (*Alter Teil*) widoczne są również odcinki bez odpowiedników w kartach. Fałdy papieru i perspektywa zdjęcia ograniczają dokładność nakładki. [Porównanie](1335-70/kontrola/porownanie-planu.jpg)
- **Jednostki.** W lipcowych wierszach kart z 20.07.1985 zarówno azymut, jak i nachylenie są w gradach. W odgałęzieniu od stacji 65 archiwalny rachunek odtwarza się w stopniach. Odcinek 4–2 ma zapis 373, równoważny 13° w tym rachunku. Ukośne kreski na polach stopniowych formularza i brak kresek na gradowych pozostawiają wątpliwość co do jednostki terenowej. W wariancie stopniowym odnoga dochodzi do strefy zawaliska narysowanej na planie. Przyjęcie gradów dla całego odgałęzienia przesuwa punkt `oct.1` o 14,57 m w rzucie. Datę 8.10.1985 przyjęto z podpisanego szkicu i arkusza obliczeń. Sam dzień pomiaru terenowego pozostaje niepotwierdzony. [Arkusz obliczeń](1335-70/zrodla/1985-10-obliczenia.jpg)
- **Współrzędne.** Obliczono od nowa położenia przed wyrównaniem i porównano ze 112 wpisami archiwalnymi. W 98 pozycjach głównego ciągu lipcowego największa różnica 3D wynosi 1,4 cm, w 8 lokalnych 0,8 cm, a w 6 dodatkowych 2,9 cm. Największa różnica dodatku wypada przy stacji 5, gdzie zapisane 11,52 m i −2,57 m dają 8,95 m, a w arkuszu wpisano 8,99 m. Stacja 12 jest poza kadrem tabeli. Łączny wektor 11–12–13 zgadza się z pozycjami stacji 11 i 13 do 0,9 cm. Te wartości mierzą zgodność odczytu i rachunku z archiwum. [Transkrypcja współrzędnych](1335-70/kontrola/wspolrzedne-archiwalne.tsv)
- **Pętla.** Dwa dojścia od 19 do 24 dają przed wyrównaniem różnicę +0,51 m na wschód, +2,51 m na północ i −2,10 m w pionie. Błąd przestrzenny wynosi **3,31 m na 131,95 m (2,51%)** i jest widoczny już w archiwalnych obliczeniach. W modelu oba dojścia kończą się na jednej stacji 24. [Raport Survex](hagen.err)
- **Odczyty kart.** Na karcie 2 suma odcinków wynosi 198,80 m przy ręcznej sumie 198,70 m, a na karcie 7 wynosi 153,25 m przy zapisanych 152,25 m. W obu przypadkach wektory potwierdzają archiwalne współrzędne. Rozróżniono 66 i 66a, zachowano pion 80–81 oraz poprawiony na karcie początek odcinka 14–82. Numeracja październikowa ma osobny prefiks `oct`.
- **Ciąg lokalny z karty 1.** Oba krótkie ramiona od stacji 2 mieszczą się przy południowym brzegu Große Halle, blisko Dohlenschacht. W tym wariancie obrys przy 1–2 jest jednak znacznie szerszy od zapisu terenowego (1 m). Cały ciąg mieści się również wewnątrz sali w innym położeniu. Rycina 276 z 1963 r. pokazuje tę samą formę, z rozbieżnością około 6 m między rysunkami. Wspólna stacja i wysokość pozostają nieustalone. [Porównanie wariantów i metoda](1335-70/kontrola/dowiazanie.md) · [Odrębny plik Survex](1335-70/lokalny.svx)

Kontrolę względem archiwum można powtórzyć poleceniem `python3 1335-70/kontrola/sprawdz.py` (Python 3.9+, `cavern`, `dump3d`). Skrypt rozdziela dwa dojścia do 24 w kopii tymczasowej i porównuje pozycje zapisane w modelu z dokładnością do 0,01 m. Po zaokrągleniu współrzędnych maksymalne różnice wynoszą odpowiednio 1,7 cm, 1,4 cm i 3,3 cm. Do odtworzenia osi w układzie drukowanego planu służy [uklad-planu.svx](1335-70/kontrola/uklad-planu.svx).

## Niemieckojęzyczne źródła

- Austriacki kataster w *Die Höhle* (1964), s. 90, wymienia 1335/70 jako *Kälbergrubenwindloch*, na południe od Brunnalm, na wysokości 1680 m. [Wpis katastralny](https://www.zobodat.at/pdf/Hoehle_015_0089-0091.pdf#page=2)
- G. Schwarzenberger, *Kälbergrubenwindloch 1335/70*, „Atlantis” (1981), zeszyt 3/4, s. 11–12. Bibliografia potwierdza publikację planu. Egzemplarz zeszytu figuruje w katalogu CNDS. W publicznie dostępnych materiałach nie udało się odnaleźć skanu tych stron ani odrębnego historycznego przekroju podłużnego. Dołączony profil W–E pochodzi z obecnej kompilacji. [Bibliografia, poz. 82.0396](https://www.ssslib.ch/bbs/download/BBS1-27%20scan/Bbs-21.pdf#page=23) · [Katalog zeszytu](https://catalogue.cnds.ffspeleo.fr/index.php?id=10653&lvl=bulletin_display)
- *Salzburger Höhlenbuch*, tom 3 (1979), s. 303–304. Hasło 1335/70 podaje także nazwę *Sturmloch* oraz historyczne parametry 270 m długości, 160 m rozciągłości poziomej i 40 m deniwelacji. Na s. 304 znajduje się plan F. Koppenwallnera z 1963 r. (ryc. 276). Strony 305–306 opisują inne jaskinie i rejon hal Angeralm i Fillingalm. [Strona 303](1335-70/zrodla/hoehlenbuch/s-303.jpg) · [Strona 304 z planem](1335-70/zrodla/hoehlenbuch/s-304.jpg) · [Pełny przekład czterech stron](1335-70/zrodla/hoehlenbuch/tlumaczenie-pl.md)
- Gottfried Tichy w objaśnieniach do arkusza geologicznego *94 Hallein* (1990), s. 67, zalicza Kälbergrubenwindloch do jaskiń lodowych południowego skraju masywu. [Geologische Bundesanstalt](https://opac.geologie.ac.at/ais312/dokumente/094_Hallein.pdf#page=68)
