# MOONWALK design direction

Street editorial: an independent streetwear zine meets a civic-tech tool. Type is the main visual.

- **Palette:** paper `#F7F6F2`, ink `#171717`, grey `#777777`, vermilion `#FF4D32`. Vermilion is used as a fill with ink text or for large display type only (3.1:1 on paper is too low for small text). Small grey metadata uses `#5C5C5C` to stay above 4.5:1.
- **Type:** Space Grotesk (display, uppercase, tight tracking), Manrope (body/controls). Compact uppercase metadata with wide tracking.
- **Layout:** 12-column grid, asymmetric section heads (label left, headline from column 4), thin ink rules instead of cards, square corners, hard offset shadows on buttons.
- **Motion:** 0.15s control transitions, one scan line while the model runs, clip-path image reveal, 0.5s section rise. All disabled under `prefers-reduced-motion`.
- **Honesty rules:** no fake progress (video progress is real frames), no fake counts, confidence only when the model returns it, authority is always labelled unconfirmed, contractor never guessed, nothing is submitted for the user.
- **Architecture:** stays on Streamlit. Custom CSS is injected from `moonwalk_ui.py`; headings use `role="heading"` divs because Streamlit wraps real `<h1>`-`<h3>` in containers that break grid layout.
- **Figma:** no Figma file was connected when this was built, so there is no Figma comparison. This file is the spec.
