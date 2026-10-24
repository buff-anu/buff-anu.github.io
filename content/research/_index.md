---
title: "Research"
description: "Anubhav Gupta's research: atmospheric entry and hypersonics, spacecraft GN&C and simulation, navigation and proximity operations, and planetary defense."
intro: "I work where guidance, navigation and control meet hard physical environments: the plasma around an entering vehicle, the limits of the actuators on a spacecraft, and navigation without the usual references. Each area below links to its papers; the full list is on the Publications page."

# Each area pulls its publications from bib entries whose `keywords`
# field contains the area's tag.
areas:
  - id: entry
    tag: entry
    title: "Atmospheric Entry and Hypersonics"
    summary: |
      A vehicle entering an atmosphere at hypersonic speed is wrapped in a shock layer and, near peak heating, a plasma sheath. Both bend and attenuate electromagnetic waves, which degrades optical sensing and cuts radio contact during blackout. I model that propagation from the flow physics up, and connect it to navigation and guidance during entry.
    highlights:
      - "A dispersion-operator framework that carries refractive-index modeling from Gladstone–Dale (neutral gas) to Appleton–Hartree (ionized flow) in hypersonic flowfields."
      - "Analytical models of aero-optical distortion, refraction and beam shifts through shock layers and the atmosphere, for laser communication from high-speed vehicles. This was my M.S. thesis at CU Boulder with Prof. Brian Argrow."
      - "AbRuAn, a framework for electromagnetic-wave propagation through planetary atmospheres and hypersonic plasmas, linking shock-layer models to optical sensing and communication performance."
      - "Reduced-order longitudinal controllability for low-lift re-entry, using line-of-sight landing error."
    links:
      - { label: "AbRuAn documentation", url: "https://abruan-documentation.readthedocs.io/en/develop/" }

  - id: gnc
    tag: gnc
    title: "Spacecraft GN&C and Simulation"
    summary: |
      I build the simulations that GN&C decisions rest on: attitude control with reaction wheels and thrusters, fault injection and anomaly detection, and Monte Carlo verification. Most of it is in Basilisk, the astrodynamics framework from CU Boulder's AVS Lab.
    highlights:
      - "A geometric framework for motor-constrained reaction-wheel operating limits, with a U.S. provisional patent application filed in 2026."
      - "Reaction-wheel prognostics after faults, a finalist for the IEEE Reliability Society Industry Paper Award."
      - "Reproducible Basilisk simulation with Docker, and the Basilisk workshop I taught at the 2024 AAS GN&C Conference."
    links:
      - { label: "Basilisk and Vizard demonstrations", url: "https://www.anubhavgupta.info/basilisk" }

  - id: navigation
    tag: navigation
    title: "Navigation and Proximity Operations"
    summary: |
      Navigation when the usual references are missing: without GPS, relative to another spacecraft, or from the terrain and magnetic field below.
    highlights:
      - "Relative navigation and state estimation for spacecraft proximity operations, including Kalman filtering (EKF, UKF) and sensor fusion."
      - "Magnetic navigation, pose-graph optimization and terrain-relative navigation, and formation flight of small quadcopters."
      - "An autonomous resource-exchange system for on-orbit servicing and microgravity manufacturing."

  - id: planetary-defense
    tag: planetary-defense
    title: "Planetary Defense"
    summary: |
      Moving an asteroid without touching it, and the question of who governs and pays for the attempt.
    highlights:
      - "Scalable multi-spacecraft hybrid electromagnetic strategies for non-contact asteroid deflection."
      - "The legal, institutional and funding challenges of a global governance framework for planetary defense."
      - "Session chair for small-body exploration at the AAS GN&C Conference since 2024, and for asteroid and interplanetary mission design at the 2024 AAS Astrodynamics Specialist Conference."
---
