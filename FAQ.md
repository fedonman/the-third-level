# The Third Level: questions people ask

## Standing in front of it

### In one sentence, what am I looking at?

A window on every setting of the two dials that control one bit of a quantum computer, each held for 120 ns, with the answer at each setting drawn as a height, sampled at fifty-six drive strengths and stacked up the page.

### And if I know nothing about quantum computers?

Then start here. Most quantum computers being built today keep their information in a small circuit printed on a chip and chilled to about a hundredth of a degree above absolute zero, colder than deep space. A circuit that cold can hold energy only in certain fixed amounts. Those fixed amounts are called its levels, and the circuit sits on one level or another and never in between. A Josephson junction in the circuit makes the gaps between the levels uneven, which is the whole reason the thing is usable: if every gap were identical, nothing could nudge the circuit off the bottom level without sending it climbing all the way up. The bottom two levels, 0 and 1, are the bit. The circuit is called a transmon.

To move it you send a microwave pulse down a cable, and two dials set that pulse. One is its pitch, or rather how far its pitch sits from the one the qubit answers to, a gap called the detuning. The other is how hard it pushes, called the drive. Hold a pulse at one setting and the qubit does not cross once and stop; it slides from level 0 towards level 1 and back again for as long as you hold it, and one round trip is called a fringe. Where you stop is what you get, anywhere from untouched to all the way across.

The ladder does not stop at level 1. Level 2 sits just above, and since the counting starts at the bottom, level 2 is the third level. Nothing in the move we are making wants it. What usually keeps the qubit away is that the levels are uneven: here the step from 1 up to 2 is 220 MHz smaller than the step from 0 up to 1, so a drive sized for one step is the wrong size for the other. This picture is a map of where that stops working, and it stops working two ways. It gives way completely if you park the drive halfway between the two steps, 110 MHz off, because two of its photons together match the 0 to 2 gap and even a gentle push empties most of the qubit onto level 2. It gives way by degrees everywhere else, a little more for every bit harder you push. The two axes are the two dials: detuning across, drive up.

### Why is it drawn as a stack?

Because a line has a baseline, and the eye is very good at seeing whether a curve comes all the way back down to it.

### What do the two colours mean?

Two curves ride every baseline. Magenta is the population that went where it was sent, the intended flip from off to on. Azure is the population that fell into the third level instead.

They are anti-correlated, so azure erupts exactly where magenta collapses. The height of the azure curve at a magenta null is the population that failed to come home.

### What is the indigo behind the stack?

The same calculation with the interference washed out: the fringe-free limit of the same plane, laid down as a ground. It puts the resonances where they belong without competing with the lines, and it is deliberately dim.

### Why do the bottom lines touch their baseline and the top ones not?

That is the subject of the piece.

At the bottom of the stack the drive is weak and the qubit behaves like the two-state device it is described as being in every popular account. Its nulls are exact zeros. The section falls to its baseline, once per fringe, all the way along. On the section at 3.6 MHz the median null sits 1.69 × 10⁻¹⁰ of full scale above the baseline, which at this printed width is a gap of 0.0 pixels. There is nothing there to see because there is nothing there.

At the top the drive is hard enough to reach the third level, and the nulls stop being zeros. On the top section, at a drive of 440 MHz, the median null stops 7.59 × 10⁻² of full scale short of its baseline: a visible gap of 15.8 pixels on a plate 4500 pixels wide. The middle of the picture is the crossover. At 130.9 MHz the floor is 1.49 × 10⁻³ and the gap is 0.3 pixels, which is about where it stops being a rounding error and starts being a thing you can point at.

Bottom to top, the floor climbs from 2.50 × 10⁻⁵ to 7.59 × 10⁻², a factor of 3041.

### Is the vertical height real?

No, and this is the one thing to be clear about. The vertical scale is exaggerated. Each profile is drawn 3.5 line spacings tall, a setting called gain, and that number was chosen by eye because it is the height at which the sections read as a landscape instead of a grid. It has no physical meaning.

What is real is everything else. The horizontal position of every feature is real: where a null falls in detuning is where the physics puts it. The shape of every curve is real. So are the ratios, because gain multiplies every section by the same number, so the 3041-fold climb from the bottom of the stack to the top survives any choice of it. Only the absolute height in millimetres is a decision of mine, and the fractions of full scale quoted above are the honest version of it.

### What are the two axes?

Left to right is the detuning, how far the drive frequency sits from the qubit's own, running from −300 to 340 MHz. Bottom to top is the drive amplitude, how hard you are pushing, from −60 to 440 MHz. Those are the two knobs an engineer turns at the control electronics. Vertical position therefore does two jobs at once: it says which section you are looking at, and within a section it carries the profile.

## The physics

### What is the third level?

Counting the levels from the bottom as 0, 1, 2, the third level is level 2, the first one above the pair a computation uses. It sits close: in this device the step from 1 up to 2 is 220 MHz smaller than the step from 0 up to 1. That mismatch is most of what keeps the qubit off level 2, and this plate is a map of the two places it gives way. It gives way resonantly at a detuning of 110 MHz, halfway between the two steps, where two drive photons together match the 0 to 2 gap exactly: a push of only 24 MHz puts ninety-two percent of the qubit on level 2 there, which is why an azure spike and the bright indigo ridge stand in fifty-four of the fifty-six lines. It gives way progressively as the drive grows, holding less the harder you push: an eighth of the population is on level 2 once the drive is as strong as the mismatch, and a quarter of it at 440 MHz. Both are drawn here, because the drive in this piece is held at one steady setting. A real machine has a third route to the same place: a pulse short enough to run a program in is spectrally broad, broad enough to drive the 1 to 2 step directly, which is what pulse shaping exists to suppress. Either way, keeping population out of the third level is one of the central problems in building these machines.

### Why does a two-level qubit come back to exactly zero?

Because the amplitude to be in the on state is a sum of two terms, and its modulus factorises into a function of the settings times one real oscillation. It vanishes wherever that oscillation does. That is one condition on two knobs, and one condition can be satisfied all along a curve. So every null is an exact zero, at every drive amplitude, forever.

### Why does the third level stop that?

Because the amplitude becomes a sum of three terms, and a sum of three does not factorise that way. Vanishing now needs a real part and an imaginary part to be zero at the same time. Two conditions on two knobs meet only at isolated points, so along a section the nulls are no longer zeros and the curve stops short of its baseline.

### Why does the shortfall grow with the drive?

Because reaching the third level costs drive. At the bottom of the stack the third term is negligible and the sum is effectively a sum of two, which is to say the bottom of the picture is a two-level world. Push harder and the third term stops being negligible. The stack is that transition drawn out along its own axis instead of collapsed into one plate.

### Does the floor rise on every single step?

No, and it would be wrong to claim it. The section at 321.8 MHz has a floor of 2.43 × 10⁻², slightly below the 2.52 × 10⁻² of the section beneath it at 258.2 MHz. The climb is a trend, not a staircase. Measured as a rank correlation between floor and drive it comes out at 0.968, and that is the form in which the program checks it before drawing.

## The pendant

### What is the pendant, the one that is only magenta?

The identical computation with the third level deleted. Same window, same sections, same colours, one thing removed. Every section runs down to its baseline everywhere, and no azure appears because there is nowhere for it to go.

### What does the pendant prove?

That the gap is physics and not drawing. In the principal plate the top section leaves 15.8 pixels of daylight under its nulls. In the pendant, at the same place, on the same axes, with the same gain, the same measurement gives 2.3 × 10⁻⁶ pixels, which is zero. Nothing about the way the picture is made produces that gap. Only the third level does.

## How it was drawn

### Is the sparkle along the lines real?

Yes, in this version. The bright core of each stroke is modulated by the fringe itself, the intended population measured against its own local envelope, so the texture rises on a fringe crest and falls into a null at the true fringe frequency. It marks the interference it sits on.

An earlier version modulated it with the phase of the excited-state amplitude instead. It looked much the same and meant nothing: that quantity is the free precession of the on state, and its measured correlation with the population is 0.002. It was decoration wearing the costume of a measurement, and it was removed. I mention it because the two versions are hard to tell apart by eye, which is exactly why the difference matters.

### What size does it print at?

A3, 420 × 297 mm. The plates are 4500 × 3516 px, which at 300 dpi is 381 × 297.7 mm: the height is exact and about 20 mm of paper is left at either side. That is not a framing choice to be trimmed away. The plate is 640 : 500 across to up because the window is 640 MHz of detuning by 500 MHz of drive, so the proportions are the physics and cropping to fill the sheet would cut 15.5 mm off the top and bottom of the stack.

At a different resolution it is the same piece of paper and one multiplication: the plate is exactly 15 inches wide, so the width in pixels is 15 × dpi and the height looks after itself. 600 dpi is `--width 9000 --dpi 600`, which comes out at 9000 × 7031 px and still measures 381 × 297.6 mm.

### Why fifty-six lines?

Because the plane is continuous and a stack has to decimate it. Fifty-six is how many sections fit at a height where each profile is legible. Every one of them is a full exact solve at its own drive amplitude, so changing the count changes which sections you are shown and never how any one of them is computed.

### What made it, and can I run it?

One Python file, with NumPy, SciPy and Matplotlib and nothing else. No external assets, no network, no randomness, no random seed. Run `uv run the-third-level.py` from the folder it sits in, and it writes its plates beside itself. The anharmonicity, the hold time, the number of lines, the gain, the supersampling, the output width and the dpi are all command line flags. There are three plates, all 4500 × 3516: the principal, the pendant, and a detail plate that frames the hardest-driven end of the stack where the gaps are widest.

## The harder questions

### How do I know any of this is true?

The program tests the claim before it is allowed to draw, and raises instead of rendering if the test fails. Every population it solves has to be finite and inside [0, 1], and seven further things have to hold: the two-level minima have to reach zero; they have to keep converging toward it as the sampling is refined; the three-level floor has to stay put under the same refinement; the top section's floor has to exceed 10⁻²; the floor has to climb at least a thousandfold from bottom to top; its rank correlation with the drive has to be at least 0.9; and the two-level pendant's floor across the stack has to be zero.

The measurements behind those, across 3481 sampled three-level nulls: the median null is 7.41 × 10⁻⁹ deep in a two-level world and 5.97 × 10⁻⁴ in this one, and one null in three sits above 1 percent, which is bright enough to see. Sampling four times more finely drove the two-level median down by a further factor of 16 while the three-level floor moved by 1.9 × 10⁻³, which is to say it did not move at all. That is the difference between a number that is on its way to zero and a number that has arrived somewhere.

### Is this AI art?

No generative model was involved. There is no diffusion model, no training data, no prompt. Every line in the picture is the solution of a 3 × 3 eigenvalue problem at a specific drive amplitude, and the program that does it is one file you can read. The one thing in this folder that was chosen rather than computed is how tall to draw the profiles, and that setting is named, printed in the diagnostics, and discussed above.

### What would make it fail?

A device with a much larger anharmonicity, which is the third level moved further away. But not in the way you would guess, and I had to run it to find out. At −0.5 GHz the gap does not shrink at all. It grows, to 12 percent, and the plate is still true. It is only further out, around −1.0 GHz, that the floor stops being a property of the field: it gets small enough that its value depends on how finely you sample, which is the definition of an artifact. The refinement test is what notices, and the program refuses to draw. So the failure is not the sections closing back down onto their baselines. It is the gap becoming too small to be a measurement, and the check that catches it is the one that asks whether the number moves when you look harder.

The other failure is one of reading rather than physics. If someone takes the height of a curve as a measured quantity in millimetres, they have been misled by a setting I chose. Height is drawn at 3.5 line spacings for a full population swing, and there is no true height it is 3.5 times larger than: population is a number between nought and one, and how tall to draw it is a decision, not a measurement. The horizontal position, the shape, and every ratio between sections are not decisions.
