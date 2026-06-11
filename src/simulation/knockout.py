"""Construcción del Round of 32 (asignación de terceros) y simulación de eliminatorias.

El árbol vive en config/bracket.yaml con los números de partido oficiales de FIFA.
Las rondas posteriores referencian al partido cuyo ganador juega, así que basta una
pasada en orden.
"""
from __future__ import annotations

from .match import MatchSimulator


def _round_name(mid: int) -> str:
    if 73 <= mid <= 88:
        return "R32"
    if 89 <= mid <= 96:
        return "R16"
    if 97 <= mid <= 100:
        return "QF"
    if 101 <= mid <= 102:
        return "SF"
    return "F"  # 104 (final)


def assign_thirds(qualifying_groups: list[str], third_allowed: dict[str, list[str]]) -> dict[str, str]:
    """Matching bipartito: asigna a cada ranura de ganador (clave) un grupo-tercero.

    Respeta los conjuntos permitidos. Devuelve {grupo_del_ganador: grupo_del_tercero}.
    Usa el algoritmo de Kuhn (caminos aumentantes). FIFA garantiza un emparejamiento
    perfecto para combinaciones válidas; si no lo hubiera, asigna los restantes a mano.
    """
    slots = list(third_allowed)
    available = set(qualifying_groups)
    adj = {s: [g for g in third_allowed[s] if g in available] for s in slots}

    match_group_to_slot: dict[str, str] = {}

    def try_assign(slot: str, seen: set[str]) -> bool:
        for g in adj[slot]:
            if g in seen:
                continue
            seen.add(g)
            if g not in match_group_to_slot or try_assign(match_group_to_slot[g], seen):
                match_group_to_slot[g] = slot
                return True
        return False

    for s in slots:
        try_assign(s, set())

    assignment = {slot: g for g, slot in match_group_to_slot.items()}

    # Fallback: si quedaron ranuras/grupos sin emparejar, completa arbitrariamente.
    unassigned_slots = [s for s in slots if s not in assignment]
    unassigned_groups = [g for g in available if g not in match_group_to_slot]
    for s, g in zip(unassigned_slots, unassigned_groups):
        assignment[s] = g
    return assignment


def _resolve(token: str, winners: dict, runners: dict, third_for_slot: dict, home_slot: str) -> str:
    """Resuelve un participante del R32 (WX / RX / T:...) a un nombre de equipo."""
    if token.startswith("T:"):
        return third_for_slot[home_slot]
    if token.startswith("W"):
        return winners[token[1:]]
    if token.startswith("R"):
        return runners[token[1:]]
    raise ValueError(f"Token desconocido: {token}")


def simulate_knockouts(
    winners: dict[str, str],
    runners: dict[str, str],
    third_team_of_group: dict[str, str],
    qualifying_groups: list[str],
    bracket: dict,
    sim: MatchSimulator,
) -> tuple[dict[str, str], str]:
    """Simula el cuadro completo. Devuelve (ronda_máxima_por_equipo, campeón)."""
    assignment = assign_thirds(qualifying_groups, bracket["third_allowed"])
    third_for_slot = {f"W{slot}": third_team_of_group[grp] for slot, grp in assignment.items()}

    match_winner: dict[int, str] = {}
    reached: dict[str, str] = {}

    # --- Round of 32 ---
    for m in bracket["round_of_32"]:
        home = _resolve(m["home"], winners, runners, third_for_slot, m["home"])
        away = _resolve(m["away"], winners, runners, third_for_slot, m["home"])
        reached[home] = "R32"; reached[away] = "R32"
        match_winner[m["id"]] = sim.play_knockout(home, away, neutral=True)

    # --- Rondas siguientes (octavos -> final), en orden ---
    for m in bracket["knockout_rounds"]:
        home, away = match_winner[m["home"]], match_winner[m["away"]]
        rnd = _round_name(m["id"])
        reached[home] = rnd; reached[away] = rnd
        match_winner[m["id"]] = sim.play_knockout(home, away, neutral=True)

    champion = match_winner[bracket["champion_match"]]
    return reached, champion
