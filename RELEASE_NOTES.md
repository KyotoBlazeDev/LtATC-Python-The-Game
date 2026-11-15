# LtATC v0.9.0-beta-7

## Desktop touch controls

- Enable **Touch controls** in the gameplay toolbar. Buttons grow to at least
  44 effective pixels with Tk display scaling, and radar targets are easier to
  tap. When targets overlap, the radar selects the nearest aircraft. Tap a
  flight strip to select a specific aircraft.
- Use **Pause/Resume**, **Previous/Next aircraft**, and **Clear selection**
  directly from the touch interface. Sandbox settings move into the scrolling
  sidebar to free up radar space in smaller windows.
- Swipe vertically over sidebar text, blank space, or buttons to scroll. A
  swipe starting on a button cancels its action. Swiping over an overflowing
  traffic list scrolls that list. **Controls up/down** and **Traffic up/down**
  also provide scrolling without a wheel.
- Touch mode lasts for the current session and uses the desktop operating
  system's single-touch mouse events in Tk. Multitouch and mobile builds remain
  unsupported.

## November 5 licensing update

- Original LtATC source code is now available under **GNU GPL-3.0-or-later**.
  Earlier CC0-1.0 grants remain valid for the versions released under those terms.
- Third-party resources retain their own terms. The bundled Bedstead font and
  separately referenced Modern DOS font remain CC0. The startup airport photo
  by Johannes Heel and its resized derivative are credited under the Unsplash
  License. See [README.md](README.md) for attribution and [LICENSE](LICENSE)
  for the GNU GPL text.

## Running the portable edition

Extract the entire Windows x64 ZIP and launch `LtATC/LtATC.exe`. Keep
`_internal` beside the executable. The build includes its Python runtime and
stores progress in `%LOCALAPPDATA%\LtATC\progress.json`. The executable is unsigned.
