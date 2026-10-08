"""Portable, validated Sandbox snapshots. Loading never mutates a live session."""
import json
import os
from dataclasses import asdict
from math import isfinite
from pathlib import Path
from tempfile import NamedTemporaryFile

from game.aircraft import Aircraft, AircraftState
from game.constants import AIRCRAFT_LIMIT, GameMode
from game.runway import Runway
from game.simulation import Simulation
from sandbox.sandbox_manager import SandboxManager


def save_scenario(path, manager):
    sim = manager.simulation
    if sim.mode != GameMode.SANDBOX or sim.game_over or manager.challenge_active or manager.challenge_finished:
        raise ValueError("Save a regular Sandbox session before game over.")
    aircraft = []
    for plane in sim.aircraft.values():
        item = asdict(plane)
        item["state"] = plane.state.name
        aircraft.append(item)
    payload = {"version": 1, "aircraft": aircraft, "runway": asdict(sim.runway),
               "settings": {key: getattr(manager, key) for key in
                            ("traffic_rate", "weather", "time_of_day", "emergencies")},
               "simulation": {"speed": sim.speed, "training_safety": sim.training_safety,
                              "separation_warnings": sim.separation_warnings,
                              "selected_callsign": sim.selected_callsign,
                              "thresholds": [sim.safety.horizontal_warning,
                                             sim.safety.horizontal_critical, sim.safety.vertical_warning]},
               "closure_remaining": manager._closure_remaining}
    path = Path(path)
    temporary = None
    try:
        with NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as stream:
            temporary = stream.name
            json.dump(payload, stream, indent=2, allow_nan=False)
        os.replace(temporary, path)
    finally:
        if temporary:
            Path(temporary).unlink(missing_ok=True)


def load_scenario(path):
    path = Path(path)
    if path.stat().st_size > 256_000:
        raise ValueError("Scenario file is too large.")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or type(data["version"]) is not int or data["version"] != 1 or not isinstance(data["aircraft"], list) or len(data["aircraft"]) > AIRCRAFT_LIMIT:
            raise ValueError("Unsupported scenario format or aircraft limit.")
        sim = Simulation()
        sim.reset(GameMode.SANDBOX)
        for item in data["aircraft"]:
            if not isinstance(item, dict):
                raise ValueError("Invalid aircraft record.")
            if not isinstance(item["callsign"], str) or not item["callsign"].strip() or len(item["callsign"]) > 40 or not item["callsign"].isprintable():
                raise ValueError("Invalid callsign.")
            for key, low, high in (("x", -30, 730), ("y", -30, 620),
                                   ("heading", 0, 360), ("target_heading", 0, 360),
                                   ("altitude", 0, 10000), ("target_altitude", 0, 10000),
                                   ("speed", 0, 250), ("target_speed", 0, 250)):
                value = item[key]
                if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value) or not low <= value <= high:
                    raise ValueError(f"Invalid aircraft {key}.")
            for key in ("selected", "emergency", "on_runway"):
                if type(item[key]) is not bool:
                    raise ValueError(f"Invalid aircraft {key}.")
            if type(item["altitude"]) is not int or type(item["target_altitude"]) is not int:
                raise ValueError("Altitude must be a whole number.")
            destination = item.get("destination", "")
            if not isinstance(destination, str) or destination not in ("", "LAND", "NORTH", "EAST", "SOUTH", "WEST"):
                raise ValueError("Invalid aircraft destination.")
            item["state"] = AircraftState[item["state"]]
            plane = Aircraft(**item)
            if not sim.spawn_aircraft(plane):
                raise ValueError("Duplicate callsign.")
        # Preserve only the supported schematic runway; never accept arbitrary geometry.
        runway = data["runway"]
        default = asdict(Runway())
        for key in ("name", "start_x", "start_y", "end_x", "end_y"):
            if runway[key] != default[key]:
                raise ValueError("Unsupported runway geometry.")
        for key in ("closed", "arrival_enabled", "departure_enabled"):
            if type(runway[key]) is not bool:
                raise ValueError("Invalid runway flag.")
        occupied = runway["occupied_by"]
        if occupied is not None and occupied not in sim.aircraft:
            raise ValueError("Runway occupant is missing.")
        on_runway = [p.callsign for p in sim.aircraft.values() if p.on_runway]
        if on_runway != ([occupied] if occupied else []):
            raise ValueError("Runway occupancy does not match aircraft.")
        sim.runway = Runway(**runway)
        settings = data["simulation"]
        sim.set_speed(settings["speed"])
        for key in ("training_safety", "separation_warnings"):
            if type(settings[key]) is not bool:
                raise ValueError("Invalid simulation flag.")
            setattr(sim, key, settings[key])
        thresholds = settings["thresholds"]
        if not isinstance(thresholds, list) or len(thresholds) != 3 or any(type(v) not in (int, float) or not isfinite(v) for v in thresholds):
            raise ValueError("Invalid separation thresholds.")
        sim.safety.set_thresholds(*thresholds)
        selected = settings["selected_callsign"]
        if selected is not None and selected not in sim.aircraft:
            raise ValueError("Selected aircraft is missing.")
        sim.select(selected)
        manager = SandboxManager(sim)
        for plane in sim.aircraft.values():
            manager.assign_destination(plane)
        settings = data["settings"]
        for key, options in (("traffic_rate", ("Manual", "Low", "Medium", "High")),
                             ("weather", ("Clear", "Cloudy", "Rain")),
                             ("time_of_day", ("Day", "Dusk", "Night"))):
            if settings[key] not in options:
                raise ValueError(f"Invalid {key}.")
            setattr(manager, key, settings[key])
        if type(settings["emergencies"]) is not bool:
            raise ValueError("Invalid emergency setting.")
        manager.emergencies = settings["emergencies"]
        remaining = data.get("closure_remaining", 0)
        if type(remaining) not in (int, float) or not isfinite(remaining) or not 0 <= remaining <= 15 or (remaining and not sim.runway.closed):
            raise ValueError("Invalid runway closure timer.")
        manager._closure_remaining = remaining
        sim.pause()
        return manager
    except (KeyError, TypeError, OverflowError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError("Invalid scenario file.") from error
