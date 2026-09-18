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


class JFK2023(IncidentChapter):
    chapter_id = "01"
    title = "Case 1: JFK Runway Incursion (2023)"
    source_id = "DCA23LA125"
    source_url = "https://www.ntsb.gov/investigations/Pages/DCA23LA125.aspx"
    date_location = "13 Jan 2023 | New York JFK"
    summary = "AAL106 crossed runway 4L without clearance as DAL1943 began its takeoff roll."
    introduction = (("Case file", "JFK, 13 January 2023. AAL106 and DAL1943 were involved in a runway incursion. This is a simplified decision study, not a replay."),)
    evidence = "ASDE-X alerted the tower while AAL106 crossed runway 4L and DAL1943 was departing."
    decision = "A departure is rolling and another aircraft is crossing its runway. What is the immediate tower response?"
    choices = (("Cancel takeoff clearance", "cancel"), ("Wait for crossing to finish", "wait"),
               ("Clear another departure", "depart"))
    correct_action = "cancel"
    wrong_feedback = "The runway conflict needs an immediate response. The NTSB says the prompt cancellation reduced the incident's severity."
    actual_outcome = "The controller cancelled DAL1943's takeoff clearance; its crew rejected the takeoff. No one was injured."
    lesson = "Surface alerts and prompt action can reduce the severity of a runway incursion."
    runway_name = "4L"
    runway_endpoints = (180, 480, 510, 150)
    traffic = (("DAL1943", 350, 360, 0, AircraftState.LINE_UP),
               ("AAL106", 250, 315, 0, AircraftState.TAXI))


class Austin2023(IncidentChapter):
    chapter_id = "02"
    title = "Case 2: Austin in Dense Fog (2023)"
    source_id = "DCA23FA149"
    source_url = "https://www.ntsb.gov/investigations/Pages/DCA23FA149.aspx"
    date_location = "4 Feb 2023 | Austin"
    summary = "SWA708 departed runway 18L while FDX1432 approached in dense fog."
    introduction = (("Case file", "Austin, 4 February 2023. SWA708 was departing while FDX1432 approached the same runway in dense fog. This schematic is not to scale."),)
    evidence = "The tower could not see SWA708 on the runway in dense fog and lacked surface detection equipment."
    decision = "The departure's position and readiness are uncertain while an arrival closes. Which decision avoids relying on an assumption?"
    choices = (("Assume departure will clear", "assume"), ("Verify position and separate", "verify"),
               ("Ignore the arriving flight", "ignore"))
    correct_action = "verify"
    wrong_feedback = "The NTSB identified an incorrect assumption about the departure clearing the runway as the probable cause."
    actual_outcome = "FDX1432's crew initiated a missed approach after seeing SWA708 through the fog. Both aircraft continued safely."
    lesson = "In low visibility, verify runway position and maintain separation rather than assuming a departure is clear."
    runway_name = "18L"
    runway_endpoints = (350, 90, 350, 510)
    traffic = (("SWA708", 350, 360, 0, AircraftState.LINE_UP),
               ("FDX1432", 560, 360, 1200, AircraftState.APPROACH))


class Burbank2023(IncidentChapter):
    chapter_id = "03"
    title = "Case 3: Burbank Converging Traffic (2023)"
    source_id = "DCA23LA185"
    source_url = "https://data.ntsb.gov/carol-repgen/api/Aviation/ReportMain/GenerateNewestReport/106779/pdf"
    date_location = "22 Feb 2023 | Burbank"
    summary = "ASH5826 and SKW5326 lost minimum separation during a go-around and departure."
    introduction = (("Case file", "Burbank, 22 February 2023. ASH5826 approached while SKW5326 departed. Their paths converged during a go-around."),)
    evidence = "The two aircraft lost minimum separation; both crews received TCAS resolution advisories."
    decision = "An arrival is going around as a departure climbs into its path. What must guide the immediate response?"
    choices = (("Treat paths as independent", "independent"), ("Protect both flight paths", "protect"),
               ("Ignore TCAS advisories", "ignore"))
    correct_action = "protect"
    wrong_feedback = "The aircraft were not safely separated. Both crews followed TCAS advisories until clear of conflict."
    actual_outcome = "Both crews complied with TCAS resolution advisories and cleared the conflict. No injuries were reported."
    lesson = "A go-around and a departure can create a new airborne conflict; monitor both paths."
    runway_name = "33"
    runway_endpoints = (540, 480, 190, 130)
    traffic = (("ASH5826", 485, 350, 2800, AircraftState.APPROACH),
               ("SKW5326", 350, 360, 1200, AircraftState.AIRBORNE))


class JFK2024(IncidentChapter):
    chapter_id = "04"
    title = "Case 4: JFK Crossing Traffic (2024)"
    source_id = "DCA24FA164 (preliminary)"
    source_url = "https://data.ntsb.gov/carol-repgen/api/Aviation/ReportMain/GenerateNewestReport/194114/pdf"
    date_location = "17 Apr 2024 | New York JFK"
    summary = "SWR17K rejected takeoff as four aircraft crossed runway 4L."
    introduction = (("Case file", "JFK, 17 April 2024. SWR17K began a takeoff attempt while four jets crossed runway 4L. This case uses preliminary NTSB information."),)
    evidence = "A controller cleared SWR17K for takeoff; another cleared four aircraft to cross the same runway."
    decision = "Several aircraft are crossing a runway used by a departing flight. What protects the runway?"
    choices = (("Continue the takeoff", "continue"), ("Stop and resolve the conflict", "stop"),
               ("Wait for an automated alert", "alert"))
    correct_action = "stop"
    wrong_feedback = "The crossing traffic makes the runway conflict immediate. The preliminary report records a rejected takeoff."
    actual_outcome = "SWR17K's crew rejected the takeoff after seeing crossing traffic. No injuries or damage were reported."
    lesson = "Runway crossing and departure clearances must be coordinated; do not depend solely on automated alerts."
    runway_name = "4L"
    runway_endpoints = (180, 480, 510, 150)
    traffic = (("SWR17K", 360, 360, 0, AircraftState.LINE_UP),
               ("DAL29", 285, 320, 0, AircraftState.TAXI),
               ("DAL420", 310, 305, 0, AircraftState.TAXI),
               ("RPA5752", 335, 290, 0, AircraftState.TAXI),
               ("AAL2246", 360, 275, 0, AircraftState.TAXI))
