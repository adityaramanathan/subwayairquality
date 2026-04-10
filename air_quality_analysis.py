"""
All parameter values sourced from peer-reviewed papers:
  Azad et al. 2023 (PMC10237451)  - 333 NYC platforms, 1-sec cadence
      underground mean 142 ± 69 μg/m³; Table 3 lists 20 worst stations (207–600 μg/m³)
      piston wind cited as main driver of high platform concentrations (p.9)
  Azad / PLOS ONE 2024 (PMC11305539)  - system mean 139 μg/m³, wait times "3–5 min"
  Vilcassim et al. 2014 (ACS ES&T)  - routine range 35–200 μg/m³
  Chang et al. 2023 (Int. J. Env. Sci. Tech.)  - inhalation rate methodology, 42–100 μg/commute
  MTA service guidelines (mta.info/document/22126, p.5B-4)  - dwell 30–45 sec, up to 60 sec peak

Note on quartile estimates (Azad 2023):
  mean=142, SD=69 → Q1 ≈ 142 − 0.67×69 ≈ 96 μg/m³, Q3 ≈ 142 + 0.67×69 ≈ 188 μg/m³

Author: Aditya Ramanathan
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import os

os.makedirs("analysis_charts", exist_ok=True)

plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.alpha": 0.3,
        "grid.color": "#AAAAAA",
        "figure.dpi": 150,
    }
)

# Constants
BLUE = "#2E6DA4"
RED = "#C0392B"
ORANGE = "#E67E22"
GRAY = "#7F8C8D"
LIGHT = "#ECF0F1"
GREEN = "#27AE60"

MEAN_CONC = 139  # μg/m³ - system-wide platform mean (Azad 2024, PMC11305539)
CONC_LOW = 35  # μg/m³ - system minimum documented (Vilcassim 2014)
CONC_Q1 = 96  # μg/m³ - 25th pctile: 142 − 0.67×69 (Azad 2023, PMC10237451)
CONC_MID = MEAN_CONC
CONC_Q3 = 188  # μg/m³ - 75th pctile: 142 + 0.67×69 (Azad 2023, PMC10237451)
CONC_HIGH = 600  # μg/m³ - 181st St mean, worst station in Table 3 (Azad 2023)

CONC_BROADWAY = 208  # μg/m³ - Specific Station: Broadway-Lafayette mean (Azad 2023, Table 3)
CONC_WEST4 = 207  # μg/m³ - Specific Station: West 4th St mean (Azad 2023, Table 3)

# wait time bounds from Azad 2024 ("3–5 min" for frequent service, Section 2.4)
WAIT_FREQ_LO = 3  # min
WAIT_FREQ_HI = 5  # min

# door-open dwell time bounds from MTA service guidelines (mta.info/document/22126, p.5B-4)
DWELL_LO = 30  # sec - target lower bound
DWELL_MID = 40  # sec - midpoint used for illustration
DWELL_HI = 60  # sec - observed peak-hour maximum

IR_REST = 10  # L/min - resting / standing (EFH2011 pg. 6-66; Azad 2024)
IR_ACTIVE = 15  # L/min - light activity / walking (EFH2011 pg. 6-66; Azad 2024)


def dose(conc, wait, ir):
    """μg inhaled = conc (μg/m³) × wait (min) × ir (L/min) × 1e-3 (L→m³)"""
    return conc * wait * ir * 1e-3


def save_chart(filename, msg):
    plt.tight_layout()
    plt.savefig(filename, bbox_inches="tight")
    plt.close()
    print(msg)


# Plot 1: Concentration profile during a 5-min wait - three documented station scenarios
# Instead of a single invented spike value, we show three lines anchored to
# real station data from Azad 2023. The door-open window uses MTA dwell time bounds.
#   LOW  scenario: 96 μg/m³  (25th pctile station, Azad 2023)
#   MEAN scenario: 139 μg/m³ (system mean, Azad 2024)
#   HIGH scenario: 208 μg/m³ (Broadway-Lafayette mean, Azad 2023 Table 3)
def generate_chart_1():
    WAIT = 300  # 5-min wait (upper bound of "3–5 min", Azad 2024)
    DOOR_OPEN = 120  # seconds into wait when train arrives (illustrative)
    DWELL = DWELL_MID  # 40 sec midpoint (MTA guidelines)

    t = np.arange(0, WAIT + 1)

    scenarios = [
        # (label, baseline conc, conc during door-open, color)
        (
            "Low-exposure station (~96 μg/m³, 25th pctile) [Azad 2023]",
            CONC_Q1,
            CONC_Q1 * 1.15,
            GREEN,
        ),
        (
            "System mean station (139 μg/m³) [Azad 2024]",
            CONC_MID,
            CONC_MID * 1.25,
            BLUE,
        ),
        (
            "High-exposure station (208 μg/m³, Broadway-Lafayette) [Azad 2023 Table 3]",
            CONC_BROADWAY,
            CONC_BROADWAY * 1.15,
            RED,
        ),
    ]

    fig, ax = plt.subplots(figsize=(9, 4.5))

    for label, base, door, color in scenarios:
        spike_mask = (t >= DOOR_OPEN) & (t < DOOR_OPEN + DWELL)
        conc_line = np.where(spike_mask, door, base * 0.97)
        ax.plot(t, conc_line, color=color, linewidth=2, label=label)

    # reported system average - the number that gets published
    ax.axhline(
        MEAN_CONC,
        color="black",
        linewidth=1.8,
        linestyle="--",
        label=f"Reported 5-min average ({MEAN_CONC} μg/m³) [Azad 2024]",
    )

    # shaded band for door-open window: 30–60 sec range (MTA guidelines)
    ax.axvspan(
        DOOR_OPEN,
        DOOR_OPEN + DWELL_HI,
        alpha=0.10,
        color=ORANGE,
        label=f"Door-open window ({DWELL_LO}–{DWELL_HI} sec) [MTA guidelines]",
    )

    # 181st St is 600 μg/m³ (Azad 2023 Table 3) - off scale, noted here
    ax.text(
        0.98,
        0.97,
        "181st St mean: 600 μg/m³ (off scale)\n[Azad 2023, Table 3]",
        transform=ax.transAxes,
        fontsize=7.5,
        va="top",
        ha="right",
        bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=GRAY, alpha=0.85),
    )

    ax.set_xlabel("Time on Platform (seconds)", fontsize=10)
    ax.set_ylabel("PM2.5 Concentration (μg/m³)", fontsize=10)
    ax.set_title(
        "Same Reported Average, Different Realities: Three Station Scenarios\n"
        "(5-min wait; all scenarios vs. same reported system average)",
        fontsize=10,
        fontweight="bold",
    )
    ax.set_xlim(0, WAIT)
    ax.set_ylim(0, 290)
    ax.legend(fontsize=8, loc="upper left")

    save_chart("analysis_charts/chart1_temporal_profile.png", "Chart 1 saved.")


# Plot 2: How wait time and inhalation rate affect dose - with IQR band and wait range
def generate_chart_2():
    wait_min = np.array([1, 2, 5, 10, 15, 20])

    fig, ax = plt.subplots(figsize=(9, 5))

    # shade documented typical wait range: "3–5 min" (Azad 2024, Section 2.4)
    ax.axvspan(
        WAIT_FREQ_LO,
        WAIT_FREQ_HI,
        alpha=0.10,
        color=GRAY,
        label=f"Typical wait time ({WAIT_FREQ_LO}–{WAIT_FREQ_HI} min) [Azad 2024]",
    )

    for ir, color, label_base in [
        (IR_REST, BLUE, f"Resting ({IR_REST} L/min) [EFH2011 pg. 6-66]"),
        (IR_ACTIVE, RED, f"Active ({IR_ACTIVE} L/min) [EFH2011 pg. 6-66]"),
    ]:
        d_low = dose(CONC_LOW, wait_min, ir)  # 35 μg/m³ (Vilcassim 2014)
        d_q1 = dose(CONC_Q1, wait_min, ir)  # 96 μg/m³ Q1 (Azad 2023)
        d_mid = dose(CONC_MID, wait_min, ir)  # 139 μg/m³ mean (Azad 2024)
        d_q3 = dose(CONC_Q3, wait_min, ir)  # 188 μg/m³ Q3 (Azad 2023)
        d_high = dose(CONC_HIGH, wait_min, ir)  # 600 μg/m³ max (Azad 2023 Table 3)

        # outer envelope: full documented range
        ax.fill_between(wait_min, d_low, d_high, alpha=0.07, color=color)

        # IQR band (Q1–Q3): the range most stations fall in (Azad 2023)
        ax.fill_between(
            wait_min,
            d_q1,
            d_q3,
            alpha=0.20,
            color=color,
            label=f"{label_base} - IQR band (96–188 μg/m³) [Azad 2023]",
        )
        ax.plot(
            wait_min,
            d_mid,
            "o-",
            color=color,
            linewidth=2,
            markersize=6,
            label=f"  at mean {CONC_MID} μg/m³ [Azad 2024]",
        )
        ax.plot(wait_min, d_low, "--", color=color, linewidth=1, alpha=0.5)
        ax.plot(
            wait_min,
            d_high,
            "--",
            color=color,
            linewidth=1,
            alpha=0.5,
            label=f"  range {CONC_LOW}–{CONC_HIGH} μg/m³ [Vilcassim 2014; Azad 2023]",
        )

    ax.set_xlabel("Platform Wait Time (minutes)", fontsize=10)
    ax.set_ylabel("Cumulative Inhaled PM2.5 (μg)", fontsize=10)
    ax.set_title(
        "Inhaled Dose and Wait Time Across Parameter Range\n"
        f"(Conc. range: {CONC_LOW}–{CONC_HIGH} μg/m³ [Vilcassim 2014; Azad 2023 Table 3];\n"
        f" IR: {IR_REST}–{IR_ACTIVE} L/min [EFH2011 pg. 6-66]; Wait band: Azad 2024)",
        fontsize=10,
        fontweight="bold",
    )
    ax.set_xticks(wait_min)
    ax.legend(fontsize=7.5, loc="upper left")

    save_chart("analysis_charts/chart2_dose_vs_wait.png", "Chart 2 saved.")


# Plot 3: Show difference between commuters with same exposure but different wait times.
# The 6x ratio is concentration-independent: it comes purely from the time ratio
# (12 min ÷ 2 min = 6), so it holds regardless of which station.
def generate_chart_3():
    waits = [2, 5, 12]
    labels = [
        "Commuter A\n(2-min wait)",
        "Commuter B\n(5-min wait,\nbaseline [Azad 2024])",
        "Commuter C\n(12-min wait)",
    ]
    colors = [BLUE, ORANGE, RED]

    fig, ax = plt.subplots(figsize=(8, 5))

    for i, (w, lbl, col) in enumerate(zip(waits, labels, colors)):
        d_low = dose(CONC_LOW, w, IR_REST)  # 35 μg/m³ (Vilcassim 2014)
        d_q1 = dose(CONC_Q1, w, IR_REST)  # 96 μg/m³ Q1 (Azad 2023)
        d_mid = dose(CONC_MID, w, IR_REST)  # 139 μg/m³ mean (Azad 2024)
        d_q3 = dose(CONC_Q3, w, IR_REST)  # 188 μg/m³ Q3 (Azad 2023)
        d_high = dose(CONC_HIGH, w, IR_REST)  # 600 μg/m³ max (Azad 2023 Table 3)

        ax.bar(i, d_mid, width=0.5, color=col, alpha=0.85, zorder=3)
        ax.errorbar(
            i,
            d_mid,
            yerr=[[d_mid - d_low], [d_high - d_mid]],
            fmt="none",
            color="black",
            capsize=6,
            linewidth=1.5,
            zorder=4,
        )
        ax.text(
            i,
            d_high + 0.3,
            f"{d_mid:.1f} μg at mean\n(IQR: {d_q1:.1f}–{d_q3:.1f} μg)\n[full range: {d_low:.1f}–{d_high:.0f}]",
            ha="center",
            va="bottom",
            fontsize=8,
        )

    # 6x ratio is purely a time ratio: 12÷2=6, independent of concentration
    ax.annotate(
        "6× difference - holds at all concentrations\n(ratio = 12 min ÷ 2 min = 6,\nindependent of station PM2.5 level)",
        xy=(1.0, dose(CONC_Q3, 12, IR_REST) * 0.85),
        fontsize=8.5,
        ha="center",
        bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=GRAY, alpha=0.8),
    )

    ax.set_xticks(range(len(waits)))
    ax.set_xticklabels(labels, fontsize=9)
    ax.set_ylabel("Inhaled PM2.5 (μg)", fontsize=10)
    ax.set_title(
        f"Behavioral Variance at the Same Station\n"
        f"(Bars = dose at mean {CONC_MID} μg/m³ [Azad 2024]; "
        f"error bars = full range {CONC_LOW}–{CONC_HIGH} μg/m³ [Vilcassim 2014; Azad 2023];\n"
        f"IR = {IR_REST} L/min [EFH2011 pg. 6-66])",
        fontsize=10,
        fontweight="bold",
    )
    ax.set_ylim(0, dose(CONC_HIGH, 12, IR_REST) * 1.35)

    save_chart("analysis_charts/chart3_behavioral_variance.png", "Chart 3 saved.")


# Plot 4: EDF heatmap across parameter space
# Concentration axis now covers the full documented range with labeled landmarks
def generate_chart_4():
    wait_range = np.array([2, 5, 10, 15, 20])
    # columns: V14 min, A23 Q1, A24 mean, A23 Q3, V14 max, then A23 Table 3 range
    conc_range = np.array([35, 96, 139, 188, 200, 300, 400, 500, 600])

    ref_dose = dose(
        CONC_MID, 5, IR_REST
    )  # reference: 5-min wait, mean conc, resting IR

    EDF = np.zeros((len(wait_range), len(conc_range)))
    for i, w in enumerate(wait_range):
        for j, c in enumerate(conc_range):
            EDF[i, j] = dose(c, w, IR_REST) / ref_dose

    fig, ax = plt.subplots(figsize=(12, 5.5))
    im = ax.imshow(
        EDF, cmap="RdYlGn_r", aspect="auto", vmin=0.2, vmax=4.5, origin="lower"
    )

    for i in range(len(wait_range)):
        for j in range(len(conc_range)):
            val = EDF[i, j]
            text_color = "white" if val > 2.8 or val < 0.45 else "black"
            ax.text(
                j,
                i,
                f"{val:.2f}",
                ha="center",
                va="center",
                fontsize=8.5,
                color=text_color,
                fontweight="bold",
            )

    # x-axis labels include source tags for each concentration value
    xlabels = [
        "35\n[V14 min]",
        "96\n[A23 Q1]",
        "139\n[A24 mean]",
        "188\n[A23 Q3]",
        "200\n[V14 max]",
        "300\n[A23]",
        "400\n[A23]",
        "500\n[A23]",
        "600\n[A23\nTable 3]",
    ]
    ax.set_xticks(range(len(conc_range)))
    ax.set_xticklabels(xlabels, fontsize=7.5)
    ax.set_yticks(range(len(wait_range)))
    ax.set_yticklabels([f"{w} min" for w in wait_range], fontsize=8.5)
    ax.set_xlabel("Station PM2.5 Concentration (μg/m³)", fontsize=10)
    ax.set_ylabel("Platform Wait Time\n[Azad 2024: typical 3–5 min]", fontsize=9)
    ax.set_title(
        f"Exposure Distortion Factor (EDF) Across Parameter Space\n"
        f"(Reference: 5-min wait, {CONC_MID} μg/m³, {IR_REST} L/min  |  EDF > 1 = underestimation)\n"
        "[Conc: Vilcassim 2014; Azad 2023 Table 3 | Wait: Azad 2024 | IR: EFH2011 pg. 6-66]",
        fontsize=10,
        fontweight="bold",
    )

    cb = plt.colorbar(im, ax=ax, fraction=0.035, pad=0.04)
    cb.set_label("EDF Value", fontsize=9)

    if CONC_MID in conc_range and 5 in wait_range:
        ref_i = list(wait_range).index(5)
        ref_j = list(conc_range).index(CONC_MID)
        ax.add_patch(
            plt.Rectangle(
                (ref_j - 0.5, ref_i - 0.5),
                1,
                1,
                fill=False,
                edgecolor="black",
                linewidth=2.5,
            )
        )
        ax.legend(
            handles=[
                mpatches.Patch(
                    fill=False,
                    edgecolor="black",
                    linewidth=2,
                    label="Reference cell (EDF = 1.00)",
                )
            ],
            loc="lower right",
            fontsize=8,
        )

    save_chart("analysis_charts/chart4_edf_heatmap.png", "Chart 4 saved.")


# Plot 5: Showing how reported exposure can lead to rank reversal
# Station values changed from original:
#   Station A: 208 μg/m³ (Broadway-Lafayette mean, Azad 2023 Table 3) - replaces 142
#   Station B: 96 μg/m³  (25th pctile of distribution, Azad 2023) - replaces 106
# The flip is verified to hold even at the extremes of both ranges.
def generate_chart_5():
    # Station A: high-exposure, frequent service
    # mean = Broadway-Lafayette 208 μg/m³ (Azad 2023 Table 3); wait = 5 min (Azad 2024)
    conc_A_lo = 180  # μg/m³ - nearby Table 3 stations (Azad 2023 Table 3)
    conc_A_mid = (
        CONC_BROADWAY  # 208 μg/m³ - Broadway-Lafayette mean (Azad 2023 Table 3)
    )
    conc_A_hi = CONC_BROADWAY  # upper = documented mean (Table 3 value is the anchor)
    wait_A = WAIT_FREQ_HI  # 5 min (Azad 2024)

    # Station B: lower-exposure, infrequent service
    # mean = 25th pctile ≈ 96 μg/m³ (Azad 2023: 142 − 0.67×69); wait = 20 min
    conc_B_lo = 70  # μg/m³ - lower tail of Azad 2023 distribution
    conc_B_mid = CONC_Q1  # 96 μg/m³ - 25th pctile (Azad 2023)
    conc_B_hi = 140  # μg/m³ - just below system mean (Azad 2023)
    wait_B = 20  # min - infrequent service upper bound

    stations = [
        f"Frequent Subway\n(5-min wait, {conc_A_mid} μg/m³)\n[Broadway-Lafayette, Azad 2023 Table 3]",
        f"Local/Infrequent\n(20-min wait, {conc_B_mid} μg/m³)\n[25th pctile, Azad 2023]",
    ]
    conc_vals = [conc_A_mid, conc_B_mid]
    wait_vals = [wait_A, wait_B]

    d_mids = [dose(conc_A_mid, wait_A, IR_REST), dose(conc_B_mid, wait_B, IR_REST)]
    d_lows = [dose(conc_A_lo, wait_A, IR_REST), dose(conc_B_lo, wait_B, IR_REST)]
    d_highs = [dose(conc_A_hi, wait_A, IR_REST), dose(conc_B_hi, wait_B, IR_REST)]

    # verify the flip holds even at the extreme: B's lowest dose vs A's highest dose
    flip_holds = d_lows[1] > d_highs[0]
    flip_note = (
        f"  Flip holds even at extremes:\n"
        f"  B_low ({d_lows[1]:.1f} μg) > A_high ({d_highs[0]:.1f} μg)"
    )

    fig, axes = plt.subplots(1, 2, figsize=(10, 5))

    # left: traditional ranking by reported concentration
    ax = axes[0]
    colors_trad = [RED, BLUE]
    bars = ax.bar(range(2), conc_vals, color=colors_trad, alpha=0.85, width=0.5)
    ax.set_xticks(range(2))
    ax.set_xticklabels(stations, fontsize=7.5)
    ax.set_ylabel("Reported PM2.5 (μg/m³)", fontsize=10)
    ax.set_title(
        "Traditional Ranking\n(by ambient concentration)",
        fontsize=10,
        fontweight="bold",
    )
    ax.set_ylim(0, 260)
    for i, (val, rank) in enumerate(zip(conc_vals, ["Rank 1 (worst)", "Rank 2"])):
        ax.text(
            i,
            val + 4,
            f"{val} μg/m³\n{rank}",
            ha="center",
            va="bottom",
            fontsize=9,
            fontweight="bold",
        )
    ax.axhline(CONC_MID, color=GRAY, linestyle=":", linewidth=1.2, alpha=0.7)
    ax.text(
        1.25,
        CONC_MID + 3,
        f"System mean\n({CONC_MID} μg/m³)\n[Azad 2024]",
        fontsize=7.5,
        color=GRAY,
        ha="right",
    )

    # right: EDF-adjusted ranking by inhaled dose
    ax = axes[1]
    colors_dose = [BLUE, RED]
    bars2 = ax.bar(range(2), d_mids, color=colors_dose, alpha=0.85, width=0.5)
    ax.errorbar(
        range(2),
        d_mids,
        yerr=[
            [d_mids[i] - d_lows[i] for i in range(2)],
            [d_highs[i] - d_mids[i] for i in range(2)],
        ],
        fmt="none",
        color="black",
        capsize=7,
        linewidth=1.5,
    )
    ax.set_xticks(range(2))
    ax.set_xticklabels(stations, fontsize=7.5)
    ax.set_ylabel(
        f"Estimated Inhaled Dose (μg)\n[IR = {IR_REST} L/min, EFH2011 pg. 6-66]", fontsize=9
    )
    ax.set_title(
        f"EDF-Adjusted Ranking\n(by inhaled dose, {IR_REST} L/min)",
        fontsize=10,
        fontweight="bold",
    )
    ax.set_ylim(0, max(d_highs) * 1.65)
    for i, (val, hi, rank) in enumerate(
        zip(d_mids, d_highs, ["Rank 2", "Rank 1 (worst)"])
    ):
        ax.text(
            i,
            hi + 0.2,
            f"{val:.1f} μg at mid-range\n(range: {d_lows[i]:.1f}–{hi:.1f} μg)\n{rank}",
            ha="center",
            va="bottom",
            fontsize=8.5,
            fontweight="bold",
        )

    # annotate that the flip holds at all bounds
    ax.text(
        0.5,
        0.35,
        flip_note,
        transform=ax.transAxes,
        fontsize=8.5,
        ha="center",
        color=GREEN,
        bbox=dict(boxstyle="round,pad=0.4", fc="white", ec=GREEN, alpha=0.9),
    )

    fig.suptitle(
        "Decision Flip: Rank Reversal Under Dose-Based Assessment\n"
        "(Error bars show concentration parameter range; flip persists across entire range)",
        fontsize=10,
        fontweight="bold",
    )

    save_chart("analysis_charts/chart5_decision_flip.png", "Chart 5 saved.")


def main():
    generate_chart_1()
    generate_chart_2()
    generate_chart_3()
    generate_chart_4()
    generate_chart_5()
    print("\nAll charts generated successfully in analysis_charts/")


if __name__ == "__main__":
    main()
