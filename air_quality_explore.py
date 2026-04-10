import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os


def calculate_dose(conc, duration_min, ir_l_min):
    # Convert L to m3 for unit consistency (ug/m3 * min * m3/min = ug)
    return conc * duration_min * (ir_l_min / 1000.0)


os.makedirs("exploration_charts", exist_ok=True)

# Constants
average_conc_pm = 139
inhalation_rate = 10
alt_inhalation_rate = 15

# Plot 1: Simulation of 5-minute platform wait showing average and peaks
# from piston wind (train arrival)

wait_duration_sec = 300  # 5 minutes
spike_start_time = 120  # 2 minutes
spike_duration = 30  # 30-second spike
spike_pm = 200  # 200 ug/m3
baseline_pm = (average_conc_pm * wait_duration_sec - spike_pm * spike_duration) / (
    wait_duration_sec - spike_duration
)

time = np.arange(0, wait_duration_sec)
conc = np.full(wait_duration_sec, baseline_pm, dtype=float)
conc[spike_start_time : spike_start_time + spike_duration] = spike_pm

# Assuming IR is converted to L/sec and conc is ug/m^3 -> ug/L conversion
dose_per_sec = conc * (inhalation_rate / 60) * 0.001

total_dose = np.sum(dose_per_sec)
spike_dose = np.sum(dose_per_sec[spike_start_time : spike_start_time + spike_duration])

percent_time = (spike_duration / wait_duration_sec) * 100
percent_dose = (spike_dose / total_dose) * 100

print(f"Reported 5-min Average: {average_conc_pm:.2f} ug/m3")
print(f"Total Inhaled Dose: {total_dose:.4f} ug")
print(f"Percent Dose / Percent Time: {percent_dose/percent_time:.2f}")

plt.figure(figsize=(12, 8))
plt.plot(time, conc, label="Real-time 1s Concentration", color="black")
plt.axhline(
    y=average_conc_pm,
    color="red",
    linestyle="--",
    label=f"Reported 5-min Average ({average_conc_pm:.1f})",
)
plt.fill_between(time, conc, alpha=0.2, color="gray")
plt.title("PM2.5 with Spike vs. PM2.5 Averaged")
plt.xlabel("Wait Time (seconds)")
plt.ylabel("PM2.5 Concentration (micrograms per cubic meter)")
plt.legend()
plt.grid(True, alpha=0.3)
plt.savefig(
    "exploration_charts/instantaneous_vs.average.png",
    dpi=400,
    bbox_inches="tight",
)
plt.close()

# Plot 2:Dose vs. Wait Time

wait_times = [1, 2, 5, 10, 20]

doses_rest = [calculate_dose(average_conc_pm, t, inhalation_rate) for t in wait_times]
doses_active = [
    calculate_dose(average_conc_pm, t, alt_inhalation_rate) for t in wait_times
]

plt.figure(figsize=(12, 8))
plt.plot(wait_times, doses_rest, marker="o", label="Resting (15 L/min)", color="blue")
plt.plot(wait_times, doses_active, marker="s", label="Active (20 L/min)", color="red")
plt.title("Cumulative Inhaled Dose vs. Wait Time")
plt.xlabel("Wait Time (minutes)")
plt.ylabel("Inhaled PM2.5 ($\mu g$)")
plt.legend()
plt.grid(True, alpha=0.3)
plt.savefig("exploration_charts/dose_vs_wait_time.png", dpi=400, bbox_inches="tight")
plt.close()

# Plot 3: Two Commuter Profiles at the Same Station with Same Reported PM2.5 but Different Wait Times

# Commuter Profiles: Commuter A arrives 2 mins before train, Commuter B: Waits 12 mins before train
times = [2, 12]
labels = ["Commuter A\n(2-min wait)", "Commuter B\n(12-min wait)"]
doses = [average_conc_pm * t * (inhalation_rate / 1000.0) for t in times]

fig, ax = plt.subplots(figsize=(8, 6))
bars = ax.bar(labels, doses, color=["#3498db", "#e74c3c"], alpha=0.8)
ax.axhline(y=0, color="black", linewidth=1)
ax.set_ylabel("Actual Inhaled Dose ($\mu g$)", fontsize=12)
ax.set_title(
    "Behavioral Variance at the Same Station\n(Reported PM2.5: 139 $\mu g/m^{3}$ for both)",
    fontsize=14,
)

for bar in bars:
    height = bar.get_height()
    ax.text(
        bar.get_x() + bar.get_width() / 2.0,
        height + 0.1,
        f"{height:.2f} $\mu g$",
        ha="center",
        va="bottom",
        fontweight="bold",
    )

plt.text(
    0.5,
    max(doses) * 0.7,
    f"Variance: {doses[1]/doses[0]:.1f}x Difference",
    bbox=dict(facecolor="white", alpha=0.5),
    ha="center",
)

plt.tight_layout()
plt.savefig(
    "exploration_charts/commuter_inhaled_dose_compare.png",
    dpi=400,
    bbox_inches="tight",
)
plt.close()

# Plot 4: EDF = Actual Exposure (dose-based, μg inhaled) / Reported Exposure (average conc × time, μg)
scenarios = []

# Reported Reference: Standard 5-min wait at 140 ug/m3 with 15 L/min IR
ref_dose = calculate_dose(average_conc_pm, 5, inhalation_rate)

local = (1.0 / 1.3) * average_conc_pm
subway = average_conc_pm

print(f"Subway Train Station Concentration of PM2.5: {subway:.2f} ug/m3")
print(f"Local Train Station Concentration of PM2.5: {local:.2f} ug/m3")

types = ["Subway", "Local"]
line = [subway, local]

for wait in [2, 5, 10, 20]:
    for i in range(2):
        actual_conc = line[i]
        actual_dose = calculate_dose(actual_conc, wait, inhalation_rate)
        edf = actual_dose / ref_dose
        scenarios.append({"Wait": wait, "Line": types[i], "EDF": edf})

df_edf = pd.DataFrame(scenarios)
df_heatmap = df_edf.pivot_table(index="Wait", columns="Line", values="EDF")

plt.figure(figsize=(12, 8))
sns.heatmap(df_heatmap, annot=True, cmap="YlOrRd", cbar_kws={"label": "EDF"})
plt.title("Exposure Distortion Factor (EDF) Matrix")
plt.tight_layout()
plt.savefig("exploration_charts/edf_heatmap.png", dpi=400, bbox_inches="tight")
plt.close()
