"""
PID Speed Controller for a Brushed DC Motor
--------------------------------------------
Models a DC motor as a first-order electromechanical system and simulates
closed-loop speed control using a PID controller. Compares step response
under P, PI, and PID tuning, and reports standard performance metrics.

Motor model (transfer function derivation from first principles):
    J*dw/dt = Kt*i - b*w - Tl          (mechanical)
    L*di/dt = V - R*i - Ke*w           (electrical)

Discretized with a simple Euler integrator for transparency (no hidden
control-toolbox "magic") so the whole loop is easy to read and modify.

Author: polik (EE student)
"""

import numpy as np
import matplotlib.pyplot as plt

# ---------------------------------------------------------------------------
# Motor + electrical parameters (typical small brushed DC motor)
# ---------------------------------------------------------------------------
R = 2.0        # armature resistance (ohm)
L = 0.05       # armature inductance (H)
J = 0.0005     # rotor inertia (kg*m^2)
b = 0.0001     # viscous friction coefficient (N*m*s)
Kt = 0.05      # torque constant (N*m/A)
Ke = 0.05      # back-EMF constant (V*s/rad)
V_MAX = 12.0   # supply / actuator saturation (V)

DT = 0.001     # simulation timestep (s)
T_END = 3.0    # total sim time (s)
SETPOINT = 100.0  # target speed (rad/s)
LOAD_TORQUE_STEP_AT = 1.5  # inject a disturbance load torque (s)
LOAD_TORQUE = 0.02          # N*m


class DCMotor:
    def __init__(self):
        self.i = 0.0   # armature current (A)
        self.w = 0.0   # angular velocity (rad/s)

    def step(self, V, Tl, dt):
        di = (V - R * self.i - Ke * self.w) / L
        dw = (Kt * self.i - b * self.w - Tl) / J
        self.i += di * dt
        self.w += dw * dt
        return self.w


class PID:
    def __init__(self, kp, ki, kd, out_min=-V_MAX, out_max=V_MAX):
        self.kp, self.ki, self.kd = kp, ki, kd
        self.out_min, self.out_max = out_min, out_max
        self.integral = 0.0
        self.prev_err = 0.0

    def compute(self, setpoint, measurement, dt):
        err = setpoint - measurement
        # anti-windup: only integrate if not saturated in the same direction
        provisional_i = self.integral + err * dt
        derivative = (err - self.prev_err) / dt if dt > 0 else 0.0
        out_unclamped = self.kp * err + self.ki * provisional_i + self.kd * derivative
        out = np.clip(out_unclamped, self.out_min, self.out_max)
        if out == out_unclamped:
            self.integral = provisional_i  # only commit integral when not saturating
        self.prev_err = err
        return out


def run_sim(kp, ki, kd, label):
    motor = DCMotor()
    pid = PID(kp, ki, kd)
    n = int(T_END / DT)
    t_hist, w_hist, v_hist = [], [], []
    for k in range(n):
        t = k * DT
        Tl = LOAD_TORQUE if t >= LOAD_TORQUE_STEP_AT else 0.0
        V = pid.compute(SETPOINT, motor.w, DT)
        w = motor.step(V, Tl, DT)
        t_hist.append(t)
        w_hist.append(w)
        v_hist.append(V)
    return np.array(t_hist), np.array(w_hist), np.array(v_hist), label


def metrics(t, w, setpoint):
    final = w[-1]
    # settling time: last time error exceeds 2% band
    band = 0.02 * setpoint
    outside = np.where(np.abs(w - setpoint) > band)[0]
    settling_time = t[outside[-1]] if len(outside) else 0.0
    overshoot = (max(w) - setpoint) / setpoint * 100 if max(w) > setpoint else 0.0
    ss_error = abs(setpoint - final)
    return settling_time, overshoot, ss_error


if __name__ == "__main__":
    runs = [
        run_sim(kp=0.6, ki=0.0, kd=0.0, label="P only"),
        run_sim(kp=0.6, ki=8.0, kd=0.0, label="PI"),
        run_sim(kp=0.6, ki=8.0, kd=0.005, label="PID"),
    ]

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9, 7), sharex=True)
    for t, w, v, label in runs:
        ax1.plot(t, w, label=label)
    ax1.axhline(SETPOINT, color="k", linestyle="--", linewidth=1, label="Setpoint")
    ax1.axvline(LOAD_TORQUE_STEP_AT, color="gray", linestyle=":", linewidth=1)
    ax1.set_ylabel("Speed (rad/s)")
    ax1.set_title("DC Motor Speed Response: P vs PI vs PID (load disturbance at t=1.5s)")
    ax1.legend()
    ax1.grid(alpha=0.3)

    for t, w, v, label in runs:
        ax2.plot(t, v, label=label)
    ax2.set_ylabel("Control effort / Voltage (V)")
    ax2.set_xlabel("Time (s)")
    ax2.grid(alpha=0.3)
    ax2.legend()

    plt.tight_layout()
    plt.savefig("pid_response.png", dpi=150)
    print("Saved pid_response.png")

    print(f"\n{'Controller':<10}{'Settling time (s)':<20}{'Overshoot (%)':<16}{'SS error (rad/s)'}")
    for t, w, v, label in runs:
        st, ov, sse = metrics(t, w, SETPOINT)
        print(f"{label:<10}{st:<20.3f}{ov:<16.2f}{sse:.4f}")
