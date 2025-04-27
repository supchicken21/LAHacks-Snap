# Parkinson’s AR Game Suite  
*Immersive, movement-based rehabilitation games for Snap Spectacles built with Lens Studio + TypeScript.*

---

## 📋 Overview
We created two playful AR experiences to help people with Parkinson’s disease practice motor control, balance, and upper-body strength:

| Game | Goal | Core Action |
| ---- | ---- | ----------- |
| **Naruto Kunai Dodger** | Improve balance & fine-motor reflexes | Dodge incoming kunai while keeping steady |
| **Wii Punch Trainer** | Boost strength & hand–eye coordination | Punch floating pads only when both are green |

---

## 🌟 Inspiration
- **Naruto Kunai Dodger** draws on the frantic ninja training scenes in *Naruto*: turning kunai-dodging into a balance drill.  
- **Wii Punch Trainer** re-imagines Wii Sports boxing; precise, timed punches replace generic pad work.  
- The project is also personal—Parkinson’s took our teammate’s great-uncle far too soon.

---

## 🛠️ How It Works
### Platform & Stack
- **Hardware:** Snap Spectacles (AR smart glasses)  
- **Engine:** Snap Lens Studio  
- **Language:** TypeScript (game logic, asset orchestration, collision math)

### Core Mechanics
| Feature | Naruto Kunai Dodger | Wii Punch Trainer |
| ------- | ------------------ | ----------------- |
| **Object Spawning** | 3-D kunai projectiles in front of the user | Dual floating targets per round |
| **Tracking** | Head & hand position → collision counter | Punch velocity & accuracy (only when both pads are green) |
| **Visual Feedback** | HUD: live collision count | HUD: round timer & pad states (`green`, `red`, `0`) |

---

## ⚠️ Key Challenges
1. **Motion-tracking fidelity** – Tuned gesture thresholds to cut false hits/misses.  
2. **AR latency & jitter** – Adjusted spawn logic and surface detection to smooth frame drops.

---

## 🏆 Accomplishments
- **Impact-first design:** Rehab that feels like gaming.  
- **Snap Lens mastery:** End-to-end pipeline (assets → scripting → deployment) delivered on schedule.

---

## 🎓 What We Learned
- Cross-disciplinary teamwork = shipping on time.  
- Deep dive into Lens Studio quirks, optimization, and Snap AI features.

---
