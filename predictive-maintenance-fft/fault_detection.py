"""
Vibration-Based Fault Detection via FFT (Predictive Maintenance)
------------------------------------------------------------------
Simulates an accelerometer sampling a rotating machine (e.g. a motor on a
bearing) and detects developing mechanical faults by looking for energy at
characteristic fault frequencies in the vibration spectrum — the same basic
technique used in real industrial condition-monitoring systems.

Signal model:
  - Healthy machine: shaft rotation harmonic + broadband sensor noise.
  - Faulty machine: same rotation harmonic, PLUS amplitude modulation at the
    bearing defect frequency (a classic outer-race bearing fault signature),
    plus a small added noise floor increase (wear -> more broadband energy).

The script computes the FFT of both signals, flags any spectral peak above a
statistical noise-floor threshold near the known fault frequency, and reports
a simple health verdict automatically (a minimal automation loop you could
wire to an alert / relay-cutoff in a real deployment).

Author: polik (EE student)
"""

import numpy as np
import matplotlib.pyplot as plt

# ---------------------------------------------------------------------------
# Sampling / machine parameters
# ---------------------------------------------------------------------------
FS = 5000          # sample rate (Hz) - typical for low-cost vibration ADC
DURATION = 2.0     # seconds of data captured per "reading"
SHAFT_FREQ = 50.0  # motor shaft rotation frequency (Hz) -> 3000 RPM
BEARING_FAULT_FREQ = 187.3  # characteristic outer-race defect frequency (Hz)
FAULT_THRESHOLD_SIGMA = 6   # peak must exceed noise floor by this many std-devs

rng = np.random.default_rng(42)


def generate_signal(faulty: bool):
    t = np.arange(0, DURATION, 1 / FS)
    # Base vibration: shaft rotation + a couple of harmonics (normal machine noise)
    signal = (
        1.0 * np.sin(2 * np.pi * SHAFT_FREQ * t)
        + 0.3 * np.sin(2 * np.pi * 2 * SHAFT_FREQ * t)
        + 0.15 * np.sin(2 * np.pi * 3 * SHAFT_FREQ * t)
    )
    noise_level = 0.15
    if faulty:
        # Outer-race bearing defect: repetitive impacts -> energy concentrated
        # at the defect frequency, amplitude-modulating the carrier vibration.
        impact_train = 0.6 * np.sin(2 * np.pi * BEARING_FAULT_FREQ * t)
        signal = signal * (1 + 0.5 * np.sign(np.sin(2 * np.pi * BEARING_FAULT_FREQ * t))) 
        signal += impact_train
        noise_level = 0.22  # worn bearing -> slightly higher broadband noise
    signal += rng.normal(0, noise_level, size=t.shape)
    return t, signal


def compute_spectrum(signal, fs):
    n = len(signal)
    freqs = np.fft.rfftfreq(n, d=1 / fs)
    mags = np.abs(np.fft.rfft(signal * np.hanning(n))) / n * 2
    return freqs, mags


def diagnose(freqs, mags, fault_freq, band=3.0):
    # Estimate the "normal" noise floor from a region away from any known
    # machine harmonic, then check if energy near the fault frequency stands
    # out statistically -> automated pass/fail decision.
    floor_region = (freqs > 220) & (freqs < 400)
    floor_mean = mags[floor_region].mean()
    floor_std = mags[floor_region].std()
    band_region = (freqs > fault_freq - band) & (freqs < fault_freq + band)
    peak = mags[band_region].max()
    threshold = floor_mean + FAULT_THRESHOLD_SIGMA * floor_std
    is_fault = peak > threshold
    return peak, threshold, is_fault


if __name__ == "__main__":
    t_h, healthy = generate_signal(faulty=False)
    t_f, faulty = generate_signal(faulty=True)

    f_h, m_h = compute_spectrum(healthy, FS)
    f_f, m_f = compute_spectrum(faulty, FS)

    peak_h, thr_h, fault_h = diagnose(f_h, m_h, BEARING_FAULT_FREQ)
    peak_f, thr_f, fault_f = diagnose(f_f, m_f, BEARING_FAULT_FREQ)

    print("=== Automated Diagnosis ===")
    print(f"Healthy unit : peak={peak_h:.4f}  threshold={thr_h:.4f}  -> {'FAULT' if fault_h else 'OK'}")
    print(f"Test unit    : peak={peak_f:.4f}  threshold={thr_f:.4f}  -> {'FAULT DETECTED' if fault_f else 'OK'}")

    fig, axes = plt.subplots(2, 2, figsize=(11, 7))

    axes[0, 0].plot(t_h[:500], healthy[:500])
    axes[0, 0].set_title("Healthy machine - time domain (100 ms window)")
    axes[0, 0].set_xlabel("Time (s)")
    axes[0, 0].set_ylabel("Acceleration (g)")

    axes[0, 1].plot(t_f[:500], faulty[:500], color="firebrick")
    axes[0, 1].set_title("Faulty bearing - time domain (100 ms window)")
    axes[0, 1].set_xlabel("Time (s)")

    axes[1, 0].plot(f_h, m_h)
    axes[1, 0].axvline(BEARING_FAULT_FREQ, color="gray", linestyle="--", label="Fault freq")
    axes[1, 0].set_xlim(0, 400)
    axes[1, 0].set_title("Healthy spectrum")
    axes[1, 0].set_xlabel("Frequency (Hz)")
    axes[1, 0].set_ylabel("Magnitude")
    axes[1, 0].legend()

    axes[1, 1].plot(f_f, m_f, color="firebrick")
    axes[1, 1].axvline(BEARING_FAULT_FREQ, color="gray", linestyle="--", label="Fault freq")
    axes[1, 1].axhline(thr_f, color="orange", linestyle=":", label="Auto threshold")
    axes[1, 1].set_xlim(0, 400)
    axes[1, 1].set_title("Faulty spectrum - defect peak flagged")
    axes[1, 1].set_xlabel("Frequency (Hz)")
    axes[1, 1].legend()

    plt.tight_layout()
    plt.savefig("fault_spectrum.png", dpi=150)
    print("Saved fault_spectrum.png")
