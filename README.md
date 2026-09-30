# CCCS 610, Assignment 1: code, results and figures

Code for the report "Assignment 1" of CCCS 610 (Digital Thinking and Data Analysis), McGill University, Fall 2026, sessions 1 to 4, by Sebastián Vielmas. Every number in the report comes from a file in `results/`, written by a script in `code/`, and every figure is in `figures/`.

## Scripts

| Script | Session and stage | Writes | In the report |
| --- | --- | --- | --- |
| `m01_quebec.py` | 1, in-depth: box-counting dimension of Québec City's buildings | `results/m01-quebec.json`, `figures/m01-quebec*.png` | Fig. 1 |
| `m02_territory.py` | 2, basic: delivery territories, extended from `territory.ipynb` | `results/m02.json`, `figures/m02-basic-*.png` | Figs. 2 and 3, Table I |
| `m02_quebec_clsc.py` | 2, in-depth: Québec City's CLSCs as Voronoi sites | `results/m02-quebec-clsc.json`, `figures/m02-quebec-clsc.png` | Fig. 4, Table II |
| `m02_nunavik_airports.py` | 2, in-depth: which Nunavik airports a "large and medium airports" map keeps | `results/m02-nunavik-airports.json` | Section III.B |
| `m03_antennas.py` | 3, basic: antenna placement, extended from `antennas.ipynb` | `results/m03.json`, `figures/m03-fixed-t70.png` | Fig. 5, Table III |
| `m03_weights.py` | 3, in-depth: exact scalarization breakpoints from `results/m03.json` | `results/m03-weights.json` | Table IV |
| `m03_quebec_zap.py` | 3, in-depth: Québec City's free Wi-Fi (ZAP) by neighbourhood and building type | `results/m03-quebec-zap.json` | Section IV.B |
| `m03_nunavik_mobile.py` | 3, in-depth: mobile coverage in Nunavik, people against land | `results/m03-nunavik-mobile.json` | Section IV.B |
| `m04_coloring.py` | 4, basic: colouring the antenna graph, extended from `coloring.ipynb` | `results/m04.json`, `figures/m04-basic.png` | Fig. 6 |
| `m04_quebec_quartiers.py` | 4, in-depth: colouring the map of Québec City's 35 neighbourhoods, with an exhaustive search for the minimum | `results/m04-quebec-quartiers.json`, `figures/m04-quebec-quartiers.png` | Fig. 7 |

Each script's first lines explain what it does and give its exact command. The commands use [uv](https://docs.astral.sh/uv/) to install the libraries, for example:

```sh
uv run --with geopandas --with matplotlib python code/m02_quebec_clsc.py
```

`m02_territory.py`, `m03_antennas.py`, `m03_weights.py` and `m04_coloring.py` need no data files.

## Data

The open data files are not stored here (87 MB). Download each one into `data/` under the name in the first column. The numbers in brackets are the report's references.

| File in `data/` | Source |
| --- | --- |
| `vdq-batiments.zip` | [3] Ville de Québec, [Empreintes des bâtiments](https://www.donneesquebec.ca/recherche/dataset/empreintes-des-batiments), CC BY 4.0 |
| `ourairports-airports.zip` | [9] OurAirports, [airports.csv](https://davidmegginson.github.io/ourairports-data/airports.csv), zipped, public domain |
| `msss-installations.zip` | [10] MSSS, [Fichiers cartographiques M02 des installations et établissements](https://www.donneesquebec.ca/recherche/dataset/fichiers-cartographiques-m02-des-installations-et-etablissements), CC BY 4.0 |
| `msss-territoires-clsc-2026.zip` | [11] MSSS, [Limites territoriales des CLSC en 2026](https://www.donneesquebec.ca/recherche/dataset/limites-territoriales), CC BY 4.0 |
| `vdq-zap.geojson` | [14] Ville de Québec, [ZAP, zones d'accès public à Internet sans fil](https://www.donneesquebec.ca/recherche/dataset/vque_29), CC BY 4.0 |
| `crtc-mobile-broadband-availability.zip` | [15] CRTC, [mobile and broadband availability](https://applications.crtc.gc.ca/OpenData/CASP/COMMUNICATION%20MONITORING%20REPORTS/Telecommunications%20Overview/English/data-mobile-and-broadband-availability.zip), Table 9 |
| `nrcan-wireless-data-network.gdb.zip` | [17] Natural Resources Canada, [Atlas of Canada, Wireless Data Network](https://open.canada.ca/data/dataset/16ec36d1-b320-4dcd-b71f-94670a59095a), Open Government Licence – Canada |
| `vdq-quartier.geojson` | [23] Ville de Québec, [Quartiers](https://www.donneesquebec.ca/recherche/dataset/vque_9), CC BY 4.0 |

The files were downloaded on 29 September 2026; a later version of a file can give slightly different numbers.
