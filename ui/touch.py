"""Size classic Tk controls in effective pixels without changing their fonts."""
import math


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
