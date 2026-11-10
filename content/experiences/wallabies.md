---
id: wallabies
role: Lead Data Scientist
company: Wallabies
start: 2023-11
end: 2025-04
sectors: [sport-tech]
type: employee
summary: >-
  Product development based on football event data for several markets
  (fantasy football, data-driven scouting for professional clubs, betting).
highlights:
  - text: Neural networks predicting goals distribution in a match
    metrics:
      - label: Prediction accuracy (1X2)
        value: "+3–8 pp"
    context: >-
      The goal of the project was to build a sports betting strategy based on
      computing probabilities and comparing them with bookmaker odds.
    details:
      - Improved by 3–8 percentage points, depending on the league, the 1X2 accuracy of an existing neural network that predicted the number of goals scored by each team in a match
      - Trained a separate network for each league, instead of a single global one, to model the specific characteristics of each league
      - Added new features to the model, such as an encoding of each team's recent form
    cv_summary: >-
      PyTorch neural networks predicting each team's goal distribution: +3–8 percentage
      points of 1X2 accuracy, using one model per league and new features encoding recent form.
  - text: Supported a Serie A club in data-driven scouting
    metrics:
      - label: Scouting manual workload
        value: "-70%"
    details:
      - Developed a Python post-processing pipeline, customized for the club, that refines the shortlist of manually identified players based on its needs
      - Cut the work per shortlist from about half a day to just over an hour
    cv_summary: >-
      Python post-processing pipeline for a Serie A club's scouting: time per shortlist cut
      from half a day to just over an hour (-70%).
skills: [python, machine-learning, neural-networks, pytorch, feature-engineering, sports-analytics, team-leadership]
---
