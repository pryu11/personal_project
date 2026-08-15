"""Bay Area city reference for geographic filtering.

WORKSITE_COUNTY is only ~15% populated in the raw LCA data, but
WORKSITE_CITY is 100% populated (see Phase 1 findings) -- so we
determine Bay Area membership from city name instead of county.

City names in the raw data are messy (mixed case, trailing ", CA",
missing spaces like "sanjose"). normalize_city() collapses all of
that down to a comparable form: take the text before the first comma,
lowercase it, and drop everything but letters. E.g. "South San
Francisco," / "SOUTH SAN FRANCISCO" / "South Sanfrancisco" all
normalize to "southsanfrancisco".
"""

import re

# Representative cities per Bay Area county. Not exhaustive -- covers
# the well-known cities where tech/data LCA filings concentrate.
BAY_AREA_CITIES_BY_COUNTY = {
    "San Francisco": ["San Francisco"],
    "San Mateo": [
        "San Mateo", "Redwood City", "Redwood Shores", "Menlo Park", "East Palo Alto",
        "Foster City", "Belmont", "San Carlos", "Burlingame", "Millbrae",
        "South San Francisco", "Daly City", "Pacifica", "Half Moon Bay",
        "San Bruno", "Brisbane",
    ],
    "Santa Clara": [
        "San Jose", "Santa Clara", "Sunnyvale", "Mountain View", "Palo Alto",
        "Cupertino", "Milpitas", "Campbell", "Los Gatos", "Saratoga",
        "Los Altos", "Los Altos Hills", "Gilroy", "Morgan Hill", "Stanford",
    ],
    "Alameda": [
        "Oakland", "Berkeley", "Fremont", "Hayward", "San Leandro",
        "Pleasanton", "Livermore", "Dublin", "Union City", "Newark",
        "Alameda", "Emeryville", "Albany", "Piedmont", "Castro Valley",
    ],
    "Contra Costa": [
        "Concord", "Richmond", "Walnut Creek", "Antioch", "San Ramon",
        "Pittsburg", "Brentwood", "Martinez", "Danville", "Pleasant Hill",
        "El Cerrito", "Hercules", "Pinole", "Lafayette", "Orinda",
        "Moraga", "San Pablo", "Clayton", "Oakley",
    ],
    "Marin": [
        "San Rafael", "Novato", "Mill Valley", "Sausalito", "San Anselmo",
        "Corte Madera", "Larkspur", "Fairfax", "Tiburon", "Ross",
    ],
    "Napa": ["Napa", "American Canyon", "St. Helena", "Calistoga", "Yountville"],
    "Solano": ["Vallejo", "Fairfield", "Vacaville", "Suisun City", "Benicia", "Dixon", "Rio Vista"],
    "Sonoma": [
        "Santa Rosa", "Petaluma", "Rohnert Park", "Sonoma", "Windsor",
        "Sebastopol", "Cloverdale", "Cotati", "Healdsburg",
    ],
}


def normalize_city(raw_city):
    """Normalize a raw WORKSITE_CITY value for matching (see module docstring)."""
    if raw_city is None or (isinstance(raw_city, float) and raw_city != raw_city):  # NaN check
        return None
    first_part = str(raw_city).split(",")[0]
    return re.sub(r"[^a-z]", "", first_part.lower())


# Normalized lookup: normalized city name -> county
BAY_AREA_CITY_TO_COUNTY = {
    normalize_city(city): county
    for county, cities in BAY_AREA_CITIES_BY_COUNTY.items()
    for city in cities
}
