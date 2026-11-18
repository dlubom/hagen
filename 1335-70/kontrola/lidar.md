# LiDAR dla atlasu Hagengebirge

Stan rozpoznania na 18 listopada 2026 r. Pobrano i zdekodowano oryginalne punkty lotniczego skanowania laserowego (ALS) z portalu SAGIS dla Kälbergruben-Windloch i Tantalhöhle. Dane nadają się do lokalnego widoku Potree obok poligonu Survex. [Portal pobierania ALS](https://www.salzburg.gv.at/api5/datalinq/report/vektorpublik@alsdownload@alsdownload) · [Opis produktów ALS](https://www.salzburg.gv.at/themen/salzburg/sagis/als-befliegungen)

## Sprawdzone pliki

| Miejsce | Plik SAGIS | Zawartość i wynik kontroli |
| --- | --- | --- |
| Kälbergruben-Windloch (1335/70) | [4427453 DGM, epoka 1](https://service.salzburg.gv.at/sagisogd/archiv/raster/hoehen/laserscan/Originalpunkte/ungefiltert/DGM/4427453_dgm_op_1_m.laz) | 6,89 MB. 1 941 635 oryginalnych punktów gruntu (klasa 2), bez RGB, na arkuszu 625 × 500 m. Najbliższy punkt gruntu jest w rzucie o 0,07 m od dolnego otworu i 0,28 m od górnego. Każda ze 112 stacji modelu ma punkt powierzchni w promieniu poziomym 0,77 m. |
| Kälbergruben-Windloch (1335/70) | [4427453 DOM, epoka 2](https://service.salzburg.gv.at/sagisogd/archiv/raster/hoehen/laserscan/Originalpunkte/ungefiltert/DOM/4427453_dom_op_2_m.laz) | 2 184 427 punktów, w tym grunt i roślinność. Punkty w DOM i odpowiadającym mu DGM kończą się na E = 435 200 m w EPSG:31258, około 87 m na zachód od górnego otworu i 183 m od dolnego. |
| Tantalhöhle (1335/30) | [4427652 DOM, epoka 2](https://service.salzburg.gv.at/sagisogd/archiv/raster/hoehen/laserscan/Originalpunkte/ungefiltert/DOM/4427652_dom_op_2_m.laz) | 31,0 MB. 5 070 501 punktów (3 695 935 gruntu, pozostałe z klas roślinności 3–5), bez RGB. W promieniu 10 m od pozycji GPX jest 4010 punktów gruntu. Jeden odstający punkt klasy 4 ma Z = 9845,85 m. |

Arkusze nalotów 1:5000 sprawdzono przestrzennie po transformacji współrzędnych otworów do EPSG:31258. `44275300` obejmuje oba otwory Kälbergruben-Windloch i wszystkie stacje modelu. Dla epoki 1 indeks podaje rok 2009, projekt `Interreg2008-2010` i pole `E1_FDA3 = 10.2008`. Dla epoki 2 podaje `Tennengau2019`. Otwór Tantalhöhle leży na arkuszu `44275202` z `Innergebirg2020` w epoce 2. Arkusze nalotów i pliki LAZ mają różne podziały. Mapa statusu z lutego 2026 r. pokazuje otwory Kälbergruben-Windloch w obszarze kampanii 2026, a punkt Tantalhöhle w obszarze planowanym na 2027. Dostępność plików z tych kampanii przy otworach wymaga potwierdzenia. [Indeks ALS Flugjahre](https://service.salzburg.gv.at/ogd/client/showDetail/aa7b0528-70c1-42c4-a03f-87d2d6a452d7) · [Mapa statusu nalotów](https://static.salzburg.gv.at/sagisdaten_download/SAGIS_DATEN/ALS/ALS_Status_aktuell.pdf)

SAGIS udostępnia oryginalne punkty w ramach OGD. Land Salzburg podaje CC BY 4.0 i zapis atrybucji `Datenquelle: Land Salzburg – data.salzburg.gv.at`. Katalog ALS odsyła do wspólnego rekordu metadanych rastra DGM 1 m. Licencję oceniono na podstawie ogólnych warunków OGD i opisu udostępniania oryginalnych punktów. [Udostępnianie danych ALS](https://www.salzburg.gv.at/themen/salzburg/sagis/als-befliegungen) · [Warunki OGD](https://www.salzburg.gv.at/themen/statistik/ogd/rechtliches-und-netiquette)

## Współrzędne i wysokości

Plik DGM dla Kälbergruben-Windloch zawiera w nagłówku EPSG:31258 oraz jednostkę Z w metrach. Sprawdzone pliki DOM epoki 2 mają współrzędne zgodne z BMN M31, standardowym układem SAGIS, i brak wpisu o projekcji w nagłówku. W plikach nie ustalono układu wysokości. Survex zapisuje model w EPSG:32633, zachowując wejściowe wysokości. Dolny otwór jest punktem stałym 1661 m. Wysokość modelowa górnego otworu wynosi 1724,04 m, a podana kontrola 1729 m. [Warunki wydawania danych SAGIS](https://www.salzburg.gv.at/themen/salzburg/sagis/geobasisdaten-und-geofachdaten) · [Georeferencja Survex](../../hagen.svx) · [Otwory](../../README.md#otwory)

Najbliższe punkty gruntu LAZ na pozycjach otworów Kälbergruben-Windloch mają 1662,13 m i 1724,21 m. Odczyt bezpośrednio ze źródłowego GeoTIFF-u BEV 1 m daje odpowiednio 1661,77 m i 1724,51 m. Dla Tantalhöhle na pozycji GPX odczyty dają ok. 1677,1 m z LAZ i 1677,47 m z BEV, przy 1710 m w GPX. To porównanie próbek powierzchni w rzucie. Nad górnym otworem rzeźba zmienia się szybko, a różnice obejmują wpływ pozycji, rodzaju pomiaru i układu wysokości. BEV podaje EVRF2000 Austria (EPSG:9274) dla serii z 2024 r. [Źródłowy GeoTIFF BEV](https://data.bev.gv.at/download/ALS/DTM/20240915/ALS_DTM_CRS3035RES50000mN2700000E4550000.tif) · [Specyfikacja BEV](https://www.bev.gv.at/Services/Produkte/Digitales-Gelaendehoehenmodell/ALS-Hoehenraster.html)

## Trzecia zakładka `LiDAR`

Panel `#lidar` ładuje arkusz `4427453` po otwarciu zakładki. Chmura ma XY w EPSG:32633, a poligon i otwory pochodzą z tego samego modelu Survex co CaveView i Mapa 2D. Geometrię obu warstw przesunięto o wspólny lokalny początek sceny. Roboczy łącznik ma oddzielny symbol w legendzie. Dane 3D Tantalhöhle wymagałyby eksportu z przypiętego źródła Survex, ponieważ `h2026.geojson` ma tylko XY. [Budowanie atlasu](../../scripts/build_pages.py) · [Import h2026](../../scripts/import_h2026.py) · [Widok JKTZ](https://dlubom.github.io/jktz-mapa-3d/vendor/potree-next/jktz.html)

## Odtworzenie chmury z kolorami ortofotomapy

Skrypt przypisuje każdemu punktowi RGB z piksela ortofotomapy basemap.at pod jego pozycją XY. Używa kafli WMTS z poziomu 19 i zachowuje źródłowe wysokości SAGIS. Wynik i sumy kontrolne źródeł zapisuje w `site/lidar/cloud/`. Usługa WMTS aktualizuje zdjęcia, więc do powtórzenia kolorowania z identycznych źródeł potrzebne są kafle z sumami zapisanymi w manifeście. [Ortofotomapa i warunki użycia](https://basemap.at/orthofoto/) · [Pochodzenie chmury](../../site/lidar/cloud/provenance.json)

Do odtworzenia potrzebne są Python 3.11+, `laspy[lazrs]`, NumPy, Pillow, pyproj i PotreeConverter 2.1.5.

```sh
python3 scripts/prepare_lidar_data.py /ścieżka/do/4427453_dgm_op_1_m.laz --converter /ścieżka/do/PotreeConverter
```
