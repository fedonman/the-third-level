#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "matplotlib>=3.10",
#   "numpy>=2.3",
#   "scipy>=1.17",
# ]
# ///
# The Third Level
# Copyright (c) 2026 Vyron Vasileiadis. All rights reserved.

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path

import matplotlib as mpl

mpl.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.ndimage import maximum_filter1d

RAD_PER_NS_TO_MHZ = 1000.0 / (2.0 * np.pi)


# --------------------------------------------------------------------------- #
# Physics
# --------------------------------------------------------------------------- #


def constant_drive_field(
    detuning: np.ndarray,
    amplitude: np.ndarray,
    anharmonicity: float,
    hold_time: float,
    levels: int,
) -> np.ndarray:
    """P1, P2 and the time-averaged leakage on a (Delta, Omega) grid.

    Inputs are in rad/ns and broadcast against each other. One 3x3 real
    symmetric eigendecomposition per point; no time stepping is needed because a
    constant drive gives a time-independent Hamiltonian.
    """

    detuning, amplitude = np.broadcast_arrays(detuning, amplitude)
    size = 2 if levels == 2 else 3
    matrix = np.zeros(detuning.shape + (size, size))
    matrix[..., 0, 1] = matrix[..., 1, 0] = 0.5 * amplitude
    matrix[..., 1, 1] = detuning
    if size == 3:
        matrix[..., 1, 2] = matrix[..., 2, 1] = 0.5 * np.sqrt(2.0) * amplitude
        matrix[..., 2, 2] = 2.0 * detuning + anharmonicity

    energies, vectors = np.linalg.eigh(matrix)
    # c_k(t) = sum_n v_n[k] v_n[0] exp(-i E_n t), exact in two or three terms.
    overlap = vectors * vectors[..., 0:1, :]
    amps = np.einsum(
        "...kn,...kn->...k", overlap, np.exp(-1j * energies[..., None, :] * hold_time)
    )
    populations = np.abs(amps) ** 2
    averaged = np.einsum("...kn,...kn->...k", vectors**2, vectors[..., 0:1, :] ** 2)

    out = np.zeros(detuning.shape + (3,))
    out[..., 0] = populations[..., 1]
    if size == 3:
        out[..., 1] = populations[..., 2]
        out[..., 2] = averaged[..., 2]
    return out


@dataclass(frozen=True)
class Transmon:
    """The device. Only the anharmonicity is a real parameter of the picture."""

    anharmonicity_ghz: float = -0.220

    @property
    def anharmonicity(self) -> float:
        return self.anharmonicity_ghz * 2.0 * np.pi


@dataclass(frozen=True)
class Composition:
    """How the sections are cut, stacked and inked. Presentation only.

    ``hold_time_ns`` is the one exception: it is physics. It is how long the
    drive is imagined to stay at each setting, and it sets the fringe spacing.
    """

    detuning_lo_mhz: float = -300.0
    detuning_hi_mhz: float = 340.0
    amplitude_lo_mhz: float = -60.0
    amplitude_hi_mhz: float = 440.0
    hold_time_ns: float = 120.0

    # The stack. `lines` is how many drive amplitudes are drawn out of the
    # continuum; `gain` is how tall each profile stands, in line spacings, and
    # is pure exaggeration with no physical meaning.
    lines: int = 56
    gain: float = 3.5
    skirt: float = 1.4

    # Fractions of the image, not pixel counts, so the plate looks the same at
    # preview size and at print size.
    stroke_frac: float = 0.00086
    glow_frac: float = 0.00286
    envelope_frac: float = 0.029
    margin_frac: float = 0.005

    supersample: int = 2
    exposure: float = 1.0

    @property
    def window(self) -> tuple[float, float, float, float]:
        return (
            self.detuning_lo_mhz,
            self.detuning_hi_mhz,
            self.amplitude_lo_mhz,
            self.amplitude_hi_mhz,
        )

    @property
    def bottom_margin_frac(self) -> float:
        """Where the nearest baseline sits, up from the bottom edge.

        A profile only ever rises from its own baseline, so this is also the
        empty ground under the whole stack.
        """

        return self.margin_frac

    @property
    def top_margin_frac(self) -> float:
        """Where the farthest baseline sits, down from the top edge.

        Not the mirror of the bottom margin, because it is not measured to the
        same thing: the nearest baseline is the lowest ink on the plate, but the
        farthest one has a whole excursion standing on top of it. To leave the
        same visible margin at both edges, the top baseline has to sit `gain`
        spacings plus that margin below the edge, and the spacing depends in
        turn on where the baseline went. Solving

            top = margin + gain * (1 - top - margin) / (lines - 1)

        puts the tallest crest the stack can reach exactly `margin_frac` under
        the top edge, whatever `gain` and `lines` are set to.
        """

        per_line = self.gain / (self.lines - 1)
        return (self.margin_frac + per_line * (1.0 - self.margin_frac)) / (1.0 + per_line)


# The macro window of the detail plate, in MHz. It frames the hardest-driven end
# of the stack, because that is where the gap under each null is widest and can
# be seen without measuring: roughly thirty fringes across, each one resolved.
# Its aspect ratio is the principal window's, so every plate comes out at the
# same pixel size and the three hang as a set.
DETAIL_WINDOW = (20.0, 340.0, 190.0, 440.0)

ROTATION = np.array([1.0, 0.0439, 0.3360])   # P1, electric pink, linear light
LEAKED = np.array([0.0722, 0.3324, 1.0])     # P2, the third level, azure
HAZE = np.array([0.0168, 0.0132, 0.1589])    # the atmospheric layer, indigo
SHADOW = np.array([0.10, 0.07, 0.50])        # a face turned from the light
WHITE = np.array([1.0, 0.92, 1.0])
AMBIENT = np.array([0.003, 0.003, 0.009])


def plate_height(
    frame: Composition,
    width_px: int,
    window: tuple[float, float, float, float] | None = None,
) -> int:
    """The height a plate comes out at. The window's aspect ratio decides it."""

    lo, hi, amp_lo, amp_hi = frame.window if window is None else window
    return round(width_px * (amp_hi - amp_lo) / (hi - lo))


def to_srgb(linear: np.ndarray) -> np.ndarray:
    linear = np.clip(linear, 0.0, 1.0)
    return np.where(
        linear <= 0.0031308, 12.92 * linear, 1.055 * linear ** (1 / 2.4) - 0.055
    )


def filmic(x: np.ndarray) -> np.ndarray:
    """A fixed monotonic tone curve (ACES approximation), in linear light."""

    return np.clip((x * (2.51 * x + 0.03)) / (x * (2.43 * x + 0.59) + 0.14), 0.0, 1.0)


def sections(
    model: Transmon,
    frame: Composition,
    columns: int,
    *,
    levels: int,
    window: tuple[float, float, float, float] | None = None,
) -> dict:
    """The drawn cuts: `lines` drive amplitudes, each solved exactly.

    Every row is a full solve at its own amplitude, so decimating the stack
    changes which sections are shown and nothing about how any one of them is
    computed.
    """

    lo, hi, amp_lo, amp_hi = frame.window if window is None else window
    detuning = np.linspace(lo, hi, columns) / RAD_PER_NS_TO_MHZ
    amplitude = np.linspace(amp_lo, amp_hi, frame.lines) / RAD_PER_NS_TO_MHZ
    field = constant_drive_field(
        detuning[None, :], amplitude[:, None],
        model.anharmonicity, frame.hold_time_ns, levels,
    )
    return {"p1": field[..., 0], "p2": field[..., 1],
            "amplitude_mhz": amplitude * RAD_PER_NS_TO_MHZ}


def fringe_bead(p1: np.ndarray, window_px: float) -> np.ndarray:
    """Stroke brightness, driven by the fringe measured against its envelope.

    This is the texture, and it is a measurement rather than an ornament: it
    rises on a fringe crest and falls into a null, at the true fringe frequency.

    ``window_px`` arrives as a fraction of the image width, so it is fractional;
    the filter needs a whole odd number of pixels, and at least three.
    """

    size = max(3, int(window_px) | 1)
    envelope = maximum_filter1d(p1, size, axis=-1, mode="nearest") + 1e-9
    return 0.10 + 0.90 * np.clip(p1 / envelope, 0.0, 1.0) ** 0.45


def haze_layer(
    model: Transmon, frame: Composition, shape: tuple[int, int],
    *, levels: int, window: tuple[float, float, float, float] | None = None,
) -> np.ndarray:
    """The fringe-free spectroscopic limit, as a scalar ground for the stack."""

    lo, hi, amp_lo, amp_hi = frame.window if window is None else window
    rows, columns = shape
    detuning = np.linspace(lo, hi, columns) / RAD_PER_NS_TO_MHZ
    amplitude = np.linspace(amp_lo, amp_hi, rows) / RAD_PER_NS_TO_MHZ
    out = np.empty(shape, dtype=np.float32)
    band = max(1, 40_000_000 // max(columns, 1))
    for start in range(0, rows, band):
        stop = min(start + band, rows)
        chunk = constant_drive_field(
            detuning[None, :], amplitude[start:stop, None],
            model.anharmonicity, frame.hold_time_ns, levels,
        )
        out[start:stop] = chunk[..., 2].astype(np.float32)
    return out


def compose(
    model: Transmon,
    frame: Composition,
    width_px: int,
    *,
    levels: int = 3,
    window: tuple[float, float, float, float] | None = None,
) -> np.ndarray:
    """Compute and tone map one plate. Returns an sRGB array."""

    height_px = plate_height(frame, width_px, window)
    ss = frame.supersample
    height, width = height_px * ss, width_px * ss

    cut = sections(model, frame, width, levels=levels, window=window)
    p1_all, p2_all = cut["p1"], cut["p2"]
    beads = fringe_bead(p1_all, frame.envelope_frac * width)

    ground = haze_layer(model, frame, (height, width), levels=levels, window=window)
    canvas = np.empty((height, width, 3), dtype=np.float32)
    np.multiply(ground[..., None], (0.30 * HAZE).astype(np.float32), out=canvas)
    canvas += AMBIENT.astype(np.float32)

    rows = np.arange(height)[:, None]
    top_m = frame.top_margin_frac * height
    bot_m = frame.bottom_margin_frac * height
    base = bot_m + np.arange(frame.lines) * (height - top_m - bot_m) / (frame.lines - 1)
    spacing = (height - top_m - bot_m) / (frame.lines - 1)
    stroke = max(0.6, frame.stroke_frac * width)
    glow = max(2.0, frame.glow_frac * width)
    # Compositional weighting, not perspective: the stack is drawn at 0.80 along
    # the near (bottom) edge rising to 1.00 at the far (top) one. That is the
    # opposite of aerial perspective, and deliberate: the top of the stack is
    # where the third level is doing something, and it is given the weight.
    emphasis = np.linspace(0.80, 1.00, frame.lines)

    def span(curve):
        """Vertical interval the curve covers inside each pixel column."""
        lo_ = np.minimum(curve, np.minimum(np.roll(curve, 1), np.roll(curve, -1)))
        hi_ = np.maximum(curve, np.maximum(np.roll(curve, 1), np.roll(curve, -1)))
        return 0.5 * (curve + lo_), 0.5 * (curve + hi_)

    for j in range(frame.lines - 1, -1, -1):                # far (top) to near
        p1, p2 = p1_all[j], p2_all[j]
        c1 = base[j] + frame.gain * spacing * p1
        c2 = base[j] + frame.gain * spacing * p2
        top = np.maximum(c1, c2)

        r0 = int(max(0, base[j] - glow - 2))
        r1 = int(min(height, top.max() + glow + 3))
        if r1 <= r0:
            continue
        r = rows[r0:r1]

        # Nearer sections occlude farther ones: the stack is opaque terrain.
        fill = np.clip(top[None, :] - r + 0.5, 0.0, 1.0)[..., None]
        bg = ground[r0:r1, :, None] * (0.30 * HAZE) + AMBIENT
        canvas[r0:r1] = canvas[r0:r1] * (1.0 - fill) + bg * fill

        lit = 0.5 + 0.5 * np.tanh(-np.gradient(top) / (3.5 * ss))
        body = (lit[:, None] * (p1[:, None] * ROTATION + p2[:, None] * LEAKED)
                + (1.0 - lit[:, None]) * (p1 + p2)[:, None] * SHADOW)
        skirt = np.exp(-np.clip((top[None, :] - r) / (frame.skirt * spacing), 0.0, None))
        canvas[r0:r1] += (0.30 * emphasis[j] * skirt[..., None]
                          * body[None, :, :] * fill).astype(np.float32)

        # In a two-level world there is no third level, so its curve must not be
        # drawn at all. The stroke weight has a floor that does not depend on
        # population, so without this the pendant would carry a faint azure line
        # along every baseline for a population that is exactly zero.
        strokes = [(c1, ROTATION, p1)]
        if p2_all.max() > 0.0:
            strokes.append((c2, LEAKED, p2))
        for curve, colour, pop in strokes:
            lo_, hi_ = span(curve)
            d = np.maximum(np.maximum(lo_[None, :] - r, r - hi_[None, :]), 0.0)
            core = np.exp(-(d / stroke) ** 2)
            halo = np.exp(-(d / glow) ** 2)
            w = emphasis[j] * (0.02 + 2.9 * pop ** 1.35)
            hot = np.clip(pop - 0.68, 0.0, None) * 3.2
            canvas[r0:r1] += ((core * w * beads[j])[..., None] * colour).astype(np.float32)
            canvas[r0:r1] += ((halo * w * 0.16)[..., None] * colour).astype(np.float32)
            canvas[r0:r1] += ((core * hot * beads[j] * emphasis[j])[..., None]
                              * WHITE).astype(np.float32)

    if ss > 1:
        canvas = canvas.reshape(height_px, ss, width_px, ss, 3).mean(axis=(1, 3))
    return to_srgb(filmic(canvas * frame.exposure))


# --------------------------------------------------------------------------- #
# Verification
# --------------------------------------------------------------------------- #


def profile_minima(
    model: Transmon, frame: Composition, *, levels: int, samples: int = 200_000
) -> np.ndarray:
    """Every across-fringe minimum of P1, on the sections actually drawn.

    Walking along one section crosses fringe after fringe. Each local minimum is
    how close that fringe came to bringing the population home. For two levels
    every one of them is zero. For three they are not, and the gap that leaves
    under the curve is the whole subject of this plate.

    The sampling here is far finer than the plate's own pixel grid on purpose.
    A two-level null is an exact zero at one detuning, so how small the smallest
    SAMPLE gets is a statement about the grid, not the physics; only refining it
    tells you whether the zero is real. Sections are banded so the batched
    eigendecomposition stays inside a couple of hundred megabytes.
    """

    lo, hi, _, _ = frame.window
    detuning = np.linspace(lo, hi, samples) / RAD_PER_NS_TO_MHZ
    amplitude = np.linspace(
        frame.amplitude_lo_mhz, frame.amplitude_hi_mhz, frame.lines
    ) / RAD_PER_NS_TO_MHZ
    collected = []
    band = max(1, 800_000 // samples)
    for start in range(0, frame.lines, band):
        chunk = constant_drive_field(
            detuning[None, :], amplitude[start:start + band, None],
            model.anharmonicity, frame.hold_time_ns, levels,
        )[..., 0]
        interior = chunk[:, 1:-1]
        keep = (interior < chunk[:, :-2]) & (interior < chunk[:, 2:])
        collected.append(interior[keep])
    return np.concatenate(collected)


def section_floors(
    model: Transmon, frame: Composition, *, levels: int, samples: int = 200_000
) -> np.ndarray:
    """The median across-fringe minimum of P1, one number per drawn section.

    This is the quantity the picture is about: how far each profile fails to
    return to its own baseline. It is a function of drive amplitude, and that
    dependence is the subject.
    """

    lo, hi, _, _ = frame.window
    detuning = np.linspace(lo, hi, samples) / RAD_PER_NS_TO_MHZ
    amplitude = np.linspace(
        frame.amplitude_lo_mhz, frame.amplitude_hi_mhz, frame.lines
    ) / RAD_PER_NS_TO_MHZ
    floors = np.empty(frame.lines)
    band = max(1, 800_000 // samples)
    for start in range(0, frame.lines, band):
        chunk = constant_drive_field(
            detuning[None, :], amplitude[start:start + band, None],
            model.anharmonicity, frame.hold_time_ns, levels,
        )[..., 0]
        interior = chunk[:, 1:-1]
        keep = (interior < chunk[:, :-2]) & (interior < chunk[:, 2:])
        for k in range(chunk.shape[0]):
            row = interior[k][keep[k]]
            floors[start + k] = np.median(row) if row.size else 0.0
    return floors


def baseline_gap_px(frame: Composition, floor: float, height_px: int) -> float:
    """A profile minimum, in pixels above its own baseline, at plate size."""

    spacing = (height_px * (1.0 - frame.top_margin_frac - frame.bottom_margin_frac)
               / (frame.lines - 1))
    return float(floor * frame.gain * spacing)


def verify(model: Transmon, frame: Composition, width_px: int) -> dict:
    """Reject a render whose physics, numerics or central claim do not hold.

    The claim of this plate is that the profile stops short of its baseline, that
    the shortfall is caused by the third level, and that it GROWS WITH THE DRIVE.
    All three are measured here.

    The last one is what makes the check hard to pass by accident. A floor that
    was an artifact of the grid would sit at the same height on every section; a
    floor that is the third level filling up must climb with the drive that
    fills it, and be absent altogether when |2> is deleted. So the test is a
    trend across the stack, not a single number.

    And the zeros are checked by refinement, as they must be: a two-level null is
    an exact zero at one detuning, so how small the smallest SAMPLE gets says
    something about the grid rather than the physics. Sampling four times as
    finely has to drive the two-level median down without limit while the
    three-level floor stays where it is.
    """

    amp_lo, amp_hi = frame.amplitude_lo_mhz, frame.amplitude_hi_mhz
    height_px = plate_height(frame, width_px)

    coarse, fine = 50_000, 200_000
    two_coarse = np.median(profile_minima(model, frame, levels=2, samples=coarse))
    two = profile_minima(model, frame, levels=2, samples=fine)
    three_coarse = np.median(profile_minima(model, frame, levels=3, samples=coarse))
    three = profile_minima(model, frame, levels=3, samples=fine)
    floors3 = section_floors(model, frame, levels=3, samples=fine)
    floors2 = section_floors(model, frame, levels=2, samples=fine)

    section = sections(model, frame, width_px, levels=3)
    total = section["p1"] + section["p2"]
    if not np.all(np.isfinite(total)):
        raise RuntimeError("Non-finite population in a drawn section")
    if section["p1"].min() < -1e-12 or total.max() > 1.0 + 1e-9:
        raise RuntimeError("Population outside [0, 1]")

    # The margin algebra has to actually contain the stack. The farthest section
    # is normally the tallest ink on the plate, but a nearer one can out-crest it
    # if its profile runs much higher, so measure the whole stack.
    full_excursion = baseline_gap_px(frame, 1.0, height_px)      # gain * spacing
    crests = (frame.bottom_margin_frac * height_px
              + np.arange(frame.lines) * (full_excursion / frame.gain)
              + full_excursion * section["p1"].max(axis=1))
    crest_px = float(crests.max())

    drive = np.linspace(amp_lo, amp_hi, frame.lines)
    # the top half of the stack
    pushed = drive > 0.5 * amp_hi
    # Bottom and top of the drawn stack. NOT "softest and hardest drive": the
    # amplitude window is asymmetric and opens at -60 MHz, so the bottom row is
    # already being driven at |Omega| = 60. The genuinely softest row sits a
    # little above it, where the drive passes through zero.
    bottom, top = float(floors3[0]), float(floors3[-1])
    # Does the floor climb with the drive? Rank correlation over the drawn stack.
    order = np.argsort(np.argsort(floors3))
    trend = float(np.corrcoef(np.arange(frame.lines), order)[0, 1])

    checks = {
        "sections_drawn": int(frame.lines),
        "profile_minima_sampled": int(three.size),
        "profile_minimum_median_two_level": float(np.median(two)),
        "profile_minimum_median_three_level": float(np.median(three)),
        "profile_minima_above_1pc_three_level": float(np.mean(three > 1e-2)),
        "floor_bottom_section": bottom,
        "floor_top_section": top,
        "floor_minimum_any_section": float(floors3.min()),
        "floor_climb_bottom_to_top": float(top / max(bottom, 1e-300)),
        "floor_rank_correlation_with_drive": trend,
        "floor_median_two_level_all_sections": float(np.median(floors2)),
        "baseline_gap_px_top_three_level":
            baseline_gap_px(frame, top, height_px),
        "baseline_gap_px_top_two_level":
            baseline_gap_px(frame, float(floors2[-1]), height_px),
        "floor_median_two_level_pushed_half": float(np.median(floors2[pushed])),
        "two_level_median_fell_by": float(two_coarse / max(np.median(two), 1e-300)),
        "three_level_median_drift": float(abs(np.median(three) / three_coarse - 1.0)),
        "plate_height_px": height_px,
        "margin_px": frame.margin_frac * height_px,
        "highest_crest_px": crest_px,
    }

    if crest_px > height_px:
        raise RuntimeError(
            f"The stack crests {crest_px - height_px:.1f} px past the top edge, so "
            "the derived top margin does not contain it"
        )

    if checks["profile_minimum_median_two_level"] > 1e-6:
        raise RuntimeError("Two-level profiles do not return to their baseline")
    if checks["two_level_median_fell_by"] < 4.0:
        raise RuntimeError(
            "Two-level profile minima did not converge toward zero under refinement"
        )
    if checks["three_level_median_drift"] > 0.05:
        raise RuntimeError(
            "The three-level floor moved under refinement, so it is an artifact "
            "of the sampling rather than a property of the field"
        )
    if top < 1e-2:
        raise RuntimeError(
            f"The top section still comes home ({top:.1e}); the third level is "
            "not lifting the profiles at all"
        )
    if checks["floor_climb_bottom_to_top"] < 1e3:
        raise RuntimeError(
            "The floor does not climb across the stack "
            f"({checks['floor_climb_bottom_to_top']:.1f}x), so it is a constant "
            "offset rather than the third level filling with the drive"
        )
    if trend < 0.9:
        raise RuntimeError(
            f"The floor ordering does not follow the drive (rank r={trend:.2f})"
        )
    if checks["floor_median_two_level_all_sections"] > 1e-6:
        raise RuntimeError("The two-level pendant does not close its gap")

    if checks["baseline_gap_px_top_three_level"] < 1.0:
        print(f"  warning: the gap is only "
              f"{checks['baseline_gap_px_top_three_level']:.2f} px even on the "
              "hardest-driven section; raise --width or --gain for a real plate")
    return checks


def save_plate(image: np.ndarray, path: Path, *, title: str, description: str,
               dpi: int) -> None:
    """Write the plate pixel for pixel, with no resampling anywhere."""

    plt.imsave(
        path.with_suffix(".png"), np.clip(image, 0.0, 1.0), origin="lower", dpi=dpi,
        metadata={"Title": title, "Author": "Vyron Vasileiadis",
                  "Description": description,
                  "Software": "Python, NumPy, SciPy, Matplotlib"},
    )


# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate The Third Level."
    )
    parser.add_argument("--output-dir", type=Path,
                        default=Path(__file__).resolve().parent,
                        help="Where the plates go (default: beside this script).")
    parser.add_argument("--width", type=int, default=4500,
                        help="Width of every plate in px (default 4500, which is A3 "
                             "at 300 dpi). The plate is 15 inches wide, so for any "
                             "other resolution use 15 * dpi.")
    parser.add_argument("--dpi", type=int, default=300)
    parser.add_argument("--anharmonicity", type=float, default=-0.220, metavar="GHZ",
                        help="Transmon anharmonicity in GHz (default -0.220).")
    parser.add_argument("--hold-time", type=float, default=120.0, metavar="NS",
                        help="How long the drive is held at each setting (default 120).")
    parser.add_argument("--lines", type=int, default=56,
                        help="How many drive amplitudes are drawn (default 56).")
    parser.add_argument("--gain", type=float, default=3.5,
                        help="Profile height in line spacings; pure exaggeration (default 3.5).")
    parser.add_argument("--supersample", type=int, default=2,
                        help="Oversampling per axis (default 2). Use 1 for a fast preview.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.width < 400:
        raise SystemExit("--width must be at least 400")
    if args.lines < 8:
        raise SystemExit("--lines must be at least 8")
    if args.gain <= 0.0 or args.hold_time <= 0.0:
        raise SystemExit("--gain and --hold-time must be positive")
    if args.supersample < 1:
        raise SystemExit("--supersample must be at least 1")
    if args.anharmonicity >= 0.0:
        raise SystemExit("--anharmonicity must be negative for a transmon")
    args.output_dir.mkdir(parents=True, exist_ok=True)

    model = Transmon(anharmonicity_ghz=args.anharmonicity)
    frame = Composition(hold_time_ns=args.hold_time, lines=args.lines,
                        gain=args.gain, supersample=args.supersample)

    # The three plates are a set and are hung as one, so they have to come out
    # at the same pixel size. That is a property of the two windows, checked
    # here rather than discovered after an hour of rendering.
    if plate_height(frame, args.width) != plate_height(frame, args.width, DETAIL_WINDOW):
        raise SystemExit("DETAIL_WINDOW no longer shares the plate aspect ratio")

    print("Verifying ...")
    checks = verify(model, frame, args.width)
    print(f"  floor climbs {checks['floor_bottom_section']:.1e} -> "
          f"{checks['floor_top_section']:.1e} up the stack "
          f"({checks['floor_climb_bottom_to_top']:.0f}x, rank r="
          f"{checks['floor_rank_correlation_with_drive']:.3f})")
    print(f"  top section stands "
          f"{checks['baseline_gap_px_top_three_level']:.1f} px off its baseline; "
          f"without the third level, {checks['baseline_gap_px_top_two_level']:.2f} px")

    plates = []
    print("Rendering the principal plate ...")
    image = compose(model, frame, args.width)
    save_plate(image, args.output_dir / "the-third-level",
               title="The Third Level",
               description=("The control plane of a three-level transmon cut into "
                            "sections. Magenta is the intended rotation, azure the "
                            "population lost to the third level, and the harder a "
                            "section is driven the further its nulls stop short of "
                            "their baseline."),
               dpi=args.dpi)
    plates.append(("the-third-level", image.shape))

    print("Rendering the pendant plate (third level deleted) ...")
    image = compose(model, frame, args.width, levels=2)
    save_plate(image, args.output_dir / "without-the-third-level",
               title="Without the Third Level",
               description=("The identical computation with |2> deleted. There is no "
                            "azure curve, and every profile returns exactly to its "
                            "own baseline once per fringe."),
               dpi=args.dpi)
    plates.append(("without-the-third-level", image.shape))

    print("Rendering the detail plate (the gap under the nulls) ...")
    image = compose(model, frame, args.width, window=DETAIL_WINDOW)
    save_plate(image, args.output_dir / "the-third-level-detail",
               title="The Third Level: Detail",
               description=("The hardest-driven end of the stack, re-solved across "
                            "a narrower range of drive, where the gap under each "
                            "null is widest and can be seen directly."),
               dpi=args.dpi)
    plates.append(("the-third-level-detail", image.shape))

    diagnostics = {
        "model": asdict(model),
        "composition": asdict(frame),
        "numerical_checks": checks,
        "plates": [{"name": n, "pixels": [int(s[1]), int(s[0])]} for n, s in plates],
        "randomness": "None. The program is fully deterministic.",
    }
    (args.output_dir / "diagnostics.json").write_text(
        json.dumps(diagnostics, indent=2) + "\n", encoding="utf-8"
    )

    print()
    for name, shape in plates:
        print(f"Wrote {name} at {shape[1]} x {shape[0]} px")
    print("Across-fringe profile minima: two-level median "
          f"{checks['profile_minimum_median_two_level']:.1e}, three-level median "
          f"{checks['profile_minimum_median_three_level']:.1e} "
          f"({checks['profile_minima_above_1pc_three_level']:.0%} above 1%)")
    print("  refining four-fold drove the two-level median down "
          f"{checks['two_level_median_fell_by']:.0f}x while the three-level floor "
          f"moved by {checks['three_level_median_drift']:.0e}")


if __name__ == "__main__":
    main()
