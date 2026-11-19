# 0070. Arrows on the photo, not a second stepper

Status: accepted (2026-11-19)
Phase: P1

## Context

This record supersedes the photo stepper in decision 0067. That decision stepped through a place's photos with Back and Next buttons under the photo, in the stop stepper's style but in faint ink. On a stop card both steppers show at once, and the owner found the two pairs of Back and Next too alike: a reader could press the photo's Next meaning the journey's, or the other way round.

## Decision

- **Round arrow buttons on the photo's left and right edges,** centred top to bottom, in ink on a paper disc that lets the photo show through a little. This is how image galleries step through pictures, so the arrows read as the photo's. They share no words, shape or place with the stop stepper's full-width row of Back and Next.
- **The count, "2 / 3", in the frame's bottom-right corner,** announced to screen readers as "Photo 2 / 3".
- **The arrows are buttons named "Previous photo" and "Next photo".** With either focused, the left and right arrow keys step too. They go round at the ends, as before, so the focus stays on the pressed button. They are 36 px, 44 px on touch screens.
- **The button row under the photo goes,** which gives the card back about 40 px.

## Alternatives

- **A row of thumbnails under the photo.** Clearer still, but it loads up to five more images on every card and takes more height than the row it replaces.
- **Keep the row and restyle it.** Fainter ink was already tried in 0067, and the owner still read the two as one.
- **Swipe on phones.** It can come later on top of the arrows, which work for every pointer and the keyboard.

## Consequences

The frame is unchanged, so nothing below the photo moves. The arrows cover a strip at each edge of a landscape photo.
