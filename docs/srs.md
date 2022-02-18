# Software Requirements Specification
## ATC Plugin in Python

1. Must load and parse raw flight plan from multiple sources.
    - SimBrief
    - Manually Entered
    - Simulator
2. Must calculate lateral and vertical aircraft route given waypoints and altitude constraints. 
3. Must calculate and provide optimal departue and arrival runways given weather conditions.
4. Must convert SIDs and STARs to waypoints and constraints. 
5. Must provide vectors between present A/C position and a given waypoint.