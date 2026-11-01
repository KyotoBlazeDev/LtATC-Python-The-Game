"""Size classic Tk controls in effective pixels without changing their fonts."""
import math


class TouchScroller:
    """Single-pointer panning before Button class bindings can consume input."""

    def __init__(self, root, canvases, enabled):
        self.canvases = canvases
        self.enabled = enabled
        self.gesture = None
        self.tag = f"TouchScroll{id(self)}"
        root.bind_class(self.tag, "<ButtonPress-1>", self.press)
        root.bind_class(self.tag, "<B1-Motion>", self.motion)
        root.bind_class(self.tag, "<ButtonRelease-1>", self.release)

    def attach(self, widget):
        tags = widget.bindtags()
        if self.tag not in tags:
            widget.bindtags((self.tag, *tags))

    def press(self, event):
        self.gesture = None
        if not self.enabled():
            return
        # Native menus, text editing and scrollbar thumbs keep their own input.
        if event.widget.winfo_class() not in ("Button", "Label", "Frame", "Labelframe", "Canvas"):
            return
        widget = event.widget
        canvases = self.canvases()
        while widget is not None:
            if widget in canvases and widget.yview() != (0.0, 1.0):
                self.gesture = (widget, event.widget, event.y_root, widget.yview()[0], False)
                if event.widget.winfo_class() == "Button":
                    # Defer activation until release so a swipe never issues a clearance.
                    return "break"
                return
            widget = widget.master

    def motion(self, event):
        if self.gesture is None:
            return
        canvas, source, start, fraction, dragging = self.gesture
        delta = event.y_root - start
        dragging = dragging or abs(delta) >= touch_pixels(canvas, 8)
        self.gesture = (canvas, source, start, fraction, dragging)
        if dragging:
            bounds = canvas.bbox("all")
            if bounds:
                canvas.yview_moveto(fraction - delta / max(1, bounds[3] - bounds[1]))
            return "break"

    def release(self, event):
        gesture, self.gesture = self.gesture, None
        if gesture is None:
            return
        canvas, source, start, fraction, dragging = gesture
        if source.winfo_class() == "Button":
            if not dragging and source.winfo_exists():
                x, y = event.x_root - source.winfo_rootx(), event.y_root - source.winfo_rooty()
                if 0 <= x < source.winfo_width() and 0 <= y < source.winfo_height():
                    source.invoke()
            return "break"
        if dragging:
            return "break"


def touch_pixels(widget, size=44):
    # Tk scaling is pixels per point; Windows' 100% baseline is 96/72.
    return math.ceil(size * float(widget.tk.call("tk", "scaling")) / (96 / 72))


def size_touch_control(widget, enabled):
    if widget.winfo_class() not in ("Button", "Checkbutton", "Menubutton"):
        return
    original = getattr(widget, "_touch_padding", None)
    if original is None:
        if not enabled:
            return
        original = (widget.cget("padx"), widget.cget("pady"))
        widget._touch_padding = original
    widget.configure(padx=original[0], pady=original[1])
    if enabled:
        target = touch_pixels(widget)
        # Requested dimensions include text, borders, indicators and padding.
        padx, pady = (widget.winfo_pixels(value) for value in original)
        widget.configure(
            padx=padx + max(0, math.ceil((target - widget.winfo_reqwidth()) / 2)),
            pady=pady + max(0, math.ceil((target - widget.winfo_reqheight()) / 2)))


def size_touch_tree(widget, enabled):
    size_touch_control(widget, enabled)
    for child in widget.winfo_children():
        size_touch_tree(child, enabled)
