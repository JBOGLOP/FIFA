"""Nombres en español y banderas para la presentación (dashboard / hoja)."""
from __future__ import annotations

from .config import load_yaml

TEAM_ES = {
    "Mexico": "México", "South Africa": "Sudáfrica", "South Korea": "Corea del Sur",
    "Czech Republic": "Chequia", "Canada": "Canadá", "United States": "EE.UU.",
    "Turkey": "Turquía", "Curaçao": "Curazao", "Ivory Coast": "Costa de Marfil",
    "Netherlands": "Países Bajos", "Japan": "Japón", "Germany": "Alemania",
    "Spain": "España", "Brazil": "Brasil", "Belgium": "Bélgica", "Croatia": "Croacia",
    "England": "Inglaterra", "France": "Francia", "Morocco": "Marruecos",
    "Saudi Arabia": "Arabia Saudita", "Egypt": "Egipto", "Iran": "Irán",
    "New Zealand": "Nueva Zelanda", "Cape Verde": "Cabo Verde", "Senegal": "Senegal",
    "Norway": "Noruega", "Algeria": "Argelia", "Austria": "Austria", "Jordan": "Jordania",
    "Portugal": "Portugal", "DR Congo": "RD Congo", "Uzbekistan": "Uzbekistán",
    "Panama": "Panamá", "Ghana": "Ghana", "Scotland": "Escocia", "Haiti": "Haití",
    "Switzerland": "Suiza", "Qatar": "Catar", "Bosnia and Herzegovina": "Bosnia",
    "Sweden": "Suecia", "Tunisia": "Túnez", "Australia": "Australia", "Iraq": "Irak",
    "Paraguay": "Paraguay", "Ecuador": "Ecuador", "Uruguay": "Uruguay",
    "Colombia": "Colombia", "Argentina": "Argentina",
}

_FLAGS = None


def es(team: str) -> str:
    return TEAM_ES.get(team, team)


def flag(team: str) -> str:
    global _FLAGS
    if _FLAGS is None:
        _FLAGS = load_yaml("flags.yaml")
    return _FLAGS.get(team, "")
