import polars as pl

STATIONS = {
    "EMBR": ("Embarcadero", "SF Downtown", "west"),
    "MONT": ("Montgomery St", "SF Downtown", "west"),
    "POWL": ("Powell St", "SF Downtown", "west"),
    "CIVC": ("Civic Center/UN Plaza", "SF Downtown", "west"),
    "16TH": ("16th St Mission", "SF Mission/South", "west"),
    "24TH": ("24th St Mission", "SF Mission/South", "west"),
    "GLEN": ("Glen Park", "SF Mission/South", "west"),
    "BALB": ("Balboa Park", "SF Mission/South", "west"),
    "DALY": ("Daly City", "Peninsula", "west"),
    "COLM": ("Colma", "Peninsula", "west"),
    "SSAN": ("South San Francisco", "Peninsula", "west"),
    "SBRN": ("San Bruno", "Peninsula", "west"),
    "SFIA": ("SFO Airport", "Peninsula", "west"),
    "MLBR": ("Millbrae", "Peninsula", "west"),
    "WOAK": ("West Oakland", "Oakland Core", "east"),
    "12TH": ("12th St Oakland City Center", "Oakland Core", "east"),
    "19TH": ("19th St Oakland", "Oakland Core", "east"),
    "MCAR": ("MacArthur", "Oakland Core", "east"),
    "LAKE": ("Lake Merritt", "Oakland Core", "east"),
    "FTVL": ("Fruitvale", "Oakland Core", "east"),
    "COLS": ("Coliseum", "Oakland Core", "east"),
    "OAKL": ("Oakland Airport", "Oakland Core", "east"),
    "ROCK": ("Rockridge", "Concord-Antioch line", "east"),
    "ORIN": ("Orinda", "Concord-Antioch line", "east"),
    "LAFY": ("Lafayette", "Concord-Antioch line", "east"),
    "WCRK": ("Walnut Creek", "Concord-Antioch line", "east"),
    "PHIL": ("Pleasant Hill/Contra Costa Centre", "Concord-Antioch line", "east"),
    "CONC": ("Concord", "Concord-Antioch line", "east"),
    "NCON": ("North Concord/Martinez", "Concord-Antioch line", "east"),
    "PITT": ("Pittsburg/Bay Point", "Concord-Antioch line", "east"),
    "PCTR": ("Pittsburg Center", "Concord-Antioch line", "east"),
    "ANTC": ("Antioch", "Concord-Antioch line", "east"),
    "ASHB": ("Ashby", "Berkeley-Richmond line", "east"),
    "DBRK": ("Downtown Berkeley", "Berkeley-Richmond line", "east"),
    "NBRK": ("North Berkeley", "Berkeley-Richmond line", "east"),
    "PLZA": ("El Cerrito Plaza", "Berkeley-Richmond line", "east"),
    "DELN": ("El Cerrito del Norte", "Berkeley-Richmond line", "east"),
    "RICH": ("Richmond", "Berkeley-Richmond line", "east"),
    "SANL": ("San Leandro", "Fremont line", "east"),
    "BAYF": ("Bay Fair", "Fremont line", "east"),
    "HAYW": ("Hayward", "Fremont line", "east"),
    "SHAY": ("South Hayward", "Fremont line", "east"),
    "UCTY": ("Union City", "Fremont line", "east"),
    "FRMT": ("Fremont", "Fremont line", "east"),
    "WARM": ("Warm Springs/South Fremont", "Fremont line", "east"),
    "MLPT": ("Milpitas", "South Bay", "east"),
    "BERY": ("Berryessa/North San Jose", "South Bay", "east"),
    "CAST": ("Castro Valley", "Dublin line", "east"),
    "WDUB": ("West Dublin/Pleasanton", "Dublin line", "east"),
    "DUBL": ("Dublin/Pleasanton", "Dublin line", "east"),
}

def station_frame():
    rows = []
    for code, (name, corridor, side) in STATIONS.items():
        rows.append((code, name, corridor, side))

    columns = ["station", "name", "corridor", "side"]
    return pl.DataFrame(rows, schema=columns, orient="row")
