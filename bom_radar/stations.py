STATIONS = {
    "IDR663": {
        "name": "Brisbane / Gold Coast",
        "lat": -27.718,
        "lon": 153.240,
        "range_km": 128,
    },
    "IDR071": {
        "name": "Sydney",
        "lat": -33.701,
        "lon": 150.926,
        "range_km": 128,
    },
    "IDR064": {
        "name": "Melbourne",
        "lat": -37.855,
        "lon": 144.755,
        "range_km": 128,
    },
    "IDR042": {
        "name": "Adelaide",
        "lat": -34.617,
        "lon": 138.468,
        "range_km": 128,
    },
    "IDR702": {
        "name": "Perth",
        "lat": -32.392,
        "lon": 115.867,
        "range_km": 128,
    },
    "IDR023": {
        "name": "Cairns",
        "lat": -16.819,
        "lon": 145.685,
        "range_km": 128,
    },
}

PRESET_LOCATIONS: dict[str, dict[str, tuple[float, float]]] = {
    "gold-coast": {
        "Gold Coast CBD":   (-28.016, 153.400),
        "Surfers Paradise": (-28.003, 153.430),
        "Broadbeach":       (-28.025, 153.431),
        "Robina":           (-28.074, 153.380),
        "Southport":        (-27.967, 153.403),
        "Nerang":           (-28.008, 153.335),
        "Coolangatta":      (-28.170, 153.540),
        "Tweed Heads":      (-28.178, 153.545),
    },
    "brisbane": {
        "Brisbane CBD":     (-27.470, 153.025),
        "Fortitude Valley": (-27.457, 153.037),
        "South Brisbane":   (-27.476, 153.019),
        "Ipswich":          (-27.616, 152.760),
        "Redcliffe":        (-27.228, 153.100),
        "Logan":            (-27.638, 153.110),
        "Carindale":        (-27.499, 153.099),
    },
    "sydney": {
        "Sydney CBD":       (-33.868, 151.209),
        "Parramatta":       (-33.815, 151.002),
        "Bondi":            (-33.891, 151.274),
        "Manly":            (-33.797, 151.287),
        "Cronulla":         (-34.054, 151.152),
        "Penrith":          (-33.751, 150.694),
        "Liverpool":        (-33.921, 150.923),
    },
    "melbourne": {
        "Melbourne CBD":    (-37.814, 144.963),
        "St Kilda":         (-37.868, 144.981),
        "Dandenong":        (-37.987, 145.216),
        "Geelong":          (-38.148, 144.361),
        "Frankston":        (-38.145, 145.126),
        "Essendon":         (-37.749, 144.905),
    },
}
