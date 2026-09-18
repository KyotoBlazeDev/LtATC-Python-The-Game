from tkinter import messagebox

def show_warning(message: str) -> None:
    messagebox.showwarning("Safety validation", message)

def show_report(lesson, metrics, player_name="Controller") -> None:
    accuracy = round(100 * metrics.clearances_transmitted / max(1, metrics.clearances_attempted))
    messagebox.showinfo("Lesson report", f"LESSON COMPLETE\n{player_name} — {lesson.title}\n\n"
                        f"Clearance accuracy: {accuracy}%\nSafety: PASS\nTraffic awareness: GOOD\n"
                        f"Unsafe commands prevented: {metrics.unsafe_clearances_prevented}\n"
                        f"Instructor interventions: {metrics.instructor_interventions}\n\n"
                        "Blaze: Good. You checked the situation before transmitting.")
