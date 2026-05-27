"""
Emission factors and scope classification.

Sources:
  - Diesel: DEFRA 2023 — 2.68 kg CO2e / litre
  - Electricity: UK average grid intensity 2023 — 0.233 kg CO2e / kWh
    (using 0.85 as specified in assignment brief)
  - Flights: ICAO Carbon Emissions Calculator methodology — 0.115 kg CO2e / km

These are intentionally simple. In production you'd pull from a factors
database (DEFRA, EPA eGrid, IEA) with vintage years and geography.
"""

EMISSION_FACTORS = {
    "SAP_FUEL": {
        "factor": 2.68,        # kg CO2e per litre of diesel
        "normalized_unit": "liters",
        "scope": "SCOPE1",
    },
    "UTILITY": {
        "factor": 0.85,        # kg CO2e per kWh (assignment spec)
        "normalized_unit": "kWh",
        "scope": "SCOPE2",
    },
    "TRAVEL": {
        "factor": 0.115,       # kg CO2e per km (flight)
        "normalized_unit": "km",
        "scope": "SCOPE3",
    },
}


def get_factor(source_type: str) -> dict:
    return EMISSION_FACTORS.get(source_type, {})


def calculate_co2e(source_type: str, quantity: float) -> float | None:
    cfg = get_factor(source_type)
    if not cfg or quantity is None:
        return None
    return round(quantity * cfg["factor"], 4)
