"""Source-labeled, simplified decision studies of documented ATC incidents."""

from game.aircraft import Aircraft, AircraftState
from story.story_chapter import StoryChapter


class IncidentChapter(StoryChapter):
    source_id = ""
    source_url = ""
    date_location = ""
    summary = ""
    evidence = ""
    decision = ""
    choices = ()
    correct_action = ""
    wrong_feedback = ""
    actual_outcome = ""
    lesson = ""
    runway_name = "27"
    runway_endpoints = (420, 360, 190, 360)
    traffic = ()

    def start(self, simulation, story_state):
        self.stage = "briefing"
        self.objective = f"{self.summary} Inspect the schematic traffic, then review the evidence."
        self.event_indicator = f"{self.date_location} | NTSB {self.source_id} | simplified reconstruction"
        simulation.runway.name = self.runway_name
        (simulation.runway.start_x, simulation.runway.start_y,
         simulation.runway.end_x, simulation.runway.end_y) = self.runway_endpoints
        for callsign, x, y, altitude, state in self.traffic:
            on_runway = state == AircraftState.LINE_UP
            simulation.spawn_aircraft(Aircraft(callsign, x, y, altitude=altitude,
                                               target_altitude=altitude, state=state,
                                               on_runway=on_runway))
            if on_runway:
                simulation.runway.occupied_by = callsign
        self.save_checkpoint(simulation, "Case briefing", story_state)

    def available_actions(self):
        if self.stage == "briefing":
            return (("Review evidence", "review"),)
        if self.stage == "decision":
            return self.choices
        if self.stage == "debrief":
            return (("Read actual outcome", "outcome"),)
        return ()

    def validate_clearance(self, aircraft, clearance, simulation):
        return "This case study uses the decision buttons in Story objective. Aircraft positions are schematic."

    def choose(self, action, simulation, story_state):
        if self.stage == "briefing" and action == "review":
            self.stage = "decision"
            self.objective = self.decision
            self.event_indicator = self.evidence
            self.say("Case file", self.evidence)
            self.save_checkpoint(simulation, "Evidence reviewed", story_state)
        elif self.stage == "decision":
            if action not in {value for _, value in self.choices}:
                return
            if action != self.correct_action:
                self.say("Training note", self.wrong_feedback)
                return
            self.stage = "debrief"
            self.objective = "Compare your safety decision with the documented outcome."
            self.event_indicator = f"Safety decision recorded | NTSB {self.source_id}"
            self.say("Case file", "Safety decision recorded. Read the documented outcome next.")
            self.save_checkpoint(simulation, "Safety decision", story_state)
        elif self.stage == "debrief" and action == "outcome":
            self.stage = "complete"
            self.completed = True
            self.objective = self.lesson
            self.event_indicator = f"DOCUMENTED OUTCOME | {self.actual_outcome}"
            self.say("NTSB summary", self.actual_outcome)
            self.say("Training note", self.lesson)
            if self.chapter_id == "04":
                story_state.training_complete = True


class Detroit1990(IncidentChapter):
    chapter_id = "01"
    title = "Case 1: Detroit in Dense Fog (1990)"
    source_id = "DCA91MA010"
    source_url = "https://www.ntsb.gov/investigations/Pages/DCA91MA010.aspx"
    date_location = "3 Dec 1990 | Detroit"
    summary = "NWA1482 became disoriented in dense fog and entered the runway used by departing NWA299."
    introduction = (("Case file", "Detroit, 3 December 1990. NWA1482 and NWA299 collided on the airport surface in dense fog. This is a simplified decision study, not a replay."),)
    evidence = "The taxiing DC-9's position was uncertain while the Boeing 727 began its takeoff roll. The NTSB identified delayed ATC action and confusing taxi instructions among the contributing factors."
    decision = "A taxiing aircraft is position-uncertain in dense fog near an active departure runway. What protects the runway?"
    choices = (("Stop departures and verify position", "verify"), ("Assume the taxi route is clear", "assume"),
               ("Issue another taxi instruction", "continue"))
    correct_action = "verify"
    wrong_feedback = "Low visibility and positional uncertainty require the runway operation to stop until the aircraft is positively located."
    actual_outcome = "NWA299 struck NWA1482 during takeoff. Eight people aboard the DC-9 were killed; no one aboard the 727 was injured."
    lesson = "In low visibility, treat positional uncertainty as a runway hazard and use unambiguous progressive control."
    runway_name = "3C"
    runway_endpoints = (350, 90, 350, 510)
    traffic = (("NWA299", 350, 390, 0, AircraftState.LINE_UP),
               ("NWA1482", 280, 330, 0, AircraftState.TAXI))


class LosAngeles1991(IncidentChapter):
    chapter_id = "02"
    title = "Case 2: Los Angeles Runway Collision (1991)"
    source_id = "DCA91MA018"
    source_url = "https://www.ntsb.gov/investigations/Pages/DCA91MA018.aspx"
    date_location = "1 Feb 1991 | Los Angeles"
    summary = "SKW5569 was holding on runway 24L when USA1493 was cleared to land on the same runway."
    introduction = (("Case file", "Los Angeles, 1 February 1991. USA1493 landed while SKW5569 was positioned on runway 24L awaiting takeoff. This schematic is not to scale."),)
    evidence = "The local controller lost awareness of SKW5569 after placing it on the runway and then cleared USA1493 to land."
    decision = "An aircraft is holding on the landing runway. What must happen before the arrival continues?"
    choices = (("Clear the arrival to land", "land"), ("Protect the occupied runway", "protect"),
               ("Wait for the crews to resolve it", "wait"))
    correct_action = "protect"
    wrong_feedback = "A runway cannot be treated as available while another aircraft is still positioned on it."
    actual_outcome = "USA1493 collided with SKW5569. Both aircraft were destroyed and 34 people were killed."
    lesson = "Maintain positive awareness of every runway occupant and preserve redundancy during high workload."
    runway_name = "24L"
    runway_endpoints = (540, 180, 160, 430)
    traffic = (("SKW5569", 350, 360, 0, AircraftState.LINE_UP),
               ("USA1493", 560, 220, 1100, AircraftState.APPROACH))


class StLouis1994(IncidentChapter):
    chapter_id = "03"
    title = "Case 3: St. Louis Wrong Runway (1994)"
    source_id = "CHI95MA044"
    source_url = "https://www.ntsb.gov/investigations/Pages/CHI95MA044.aspx"
    date_location = "22 Nov 1994 | St. Louis"
    summary = "N441KM entered runway 30R while TWA427 accelerated for takeoff on that runway."
    introduction = (("Case file", "St. Louis, 22 November 1994. TWA427 and N441KM collided at runway 30R and taxiway Romeo after the Cessna entered the wrong runway."),)
    evidence = "The Cessna pilot mistakenly believed runway 30R was assigned instead of runway 31, and the incursion was not detected before TWA427 departed."
    decision = "A surface aircraft appears on a departure runway inconsistent with its clearance. What is the safe response?"
    choices = (("Continue the departure", "continue"), ("Stop and verify the surface target", "verify"),
               ("Assume it will hold short", "assume"))
    correct_action = "verify"
    wrong_feedback = "A possible wrong-runway entry must be resolved before authorizing or continuing a departure."
    actual_outcome = "TWA427 struck N441KM during takeoff. Both occupants of the Cessna were killed; eight people aboard the MD-82 received minor injuries."
    lesson = "Clear phraseology, conspicuous markings, and surface surveillance help expose wrong-runway assumptions."
    runway_name = "30R"
    runway_endpoints = (530, 450, 170, 160)
    traffic = (("TWA427", 390, 340, 0, AircraftState.LINE_UP),
               ("N441KM", 315, 300, 0, AircraftState.TAXI))


class Providence1999(IncidentChapter):
    chapter_id = "04"
    title = "Case 4: Providence Surface Confusion (1999)"
    source_id = "A-00-066 through -071"
    source_url = "https://www.ntsb.gov/safety/safety-recs/RecLetters/A00_66_71.pdf"
    date_location = "6 Dec 1999 | Providence"
    summary = "UAL1448 became disoriented at night in low visibility and reported that it might be on an active runway."
    introduction = (("Case file", "Providence, 6 December 1999. UAL1448 became disoriented after landing in nighttime instrument conditions. This schematic is not to scale."),)
    evidence = "UAL1448 deviated from its taxi route and reported that it believed it was on an active runway. FDX1662 departed nearby, and another departure was subsequently cleared."
    decision = "A crew reports uncertain position and possible runway occupancy. What must happen before another departure?"
    choices = (("Suspend departures and locate the aircraft", "locate"), ("Continue because the runway looks clear", "continue"),
               ("Ask the next departure to decide", "delegate"))
    correct_action = "locate"
    wrong_feedback = "A crew's report of possible runway occupancy must be resolved before the runway is used again."
    actual_outcome = "FDX1662 departed near UAL1448. The next departure crew declined its clearance because of the uncertainty; no one was injured and no aircraft was damaged."
    lesson = "When surface position is uncertain, suspend conflicting movement and positively locate the aircraft."
    runway_name = "5R"
    runway_endpoints = (180, 470, 520, 170)
    traffic = (("UAL1448", 300, 315, 0, AircraftState.TAXI),
               ("FDX1662", 370, 360, 0, AircraftState.LINE_UP),
               ("USA2998", 450, 410, 0, AircraftState.HOLDING_SHORT))
