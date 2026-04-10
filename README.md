# NYC Subway Exposure Gap

Standard subway air quality assessments report time-averaged PM2.5 concentrations, a convention that systematically obscures the temporal and behavioral factors that drive actual inhaled dose. This project introduces the Exposure Distortion Factor (EDF), defined as the ratio of actual inhaled dose to the dose implied by the reported station average, to quantify this gap. 

This work is in progress. These are notes that will be revised over the course of the project. 

## Notes 

- At a Q1 station (96 μg/m³), 5-min wait; EDF approx. 0.69 (slightly below 1 - rare best case)
- At system mean (139 μg/m³), 5-min wait; EDF = 1.00 (by definition, the reference)
- At system mean, 10-min wait; EDF approx. 2.0
- At Broadway-Lafayette (208 μg/m³), 5-min wait; EDF approx. 1.50
- At Broadway-Lafayette, 10-min wait; EDF approx. 3.0
- At 181st St (600 μg/m³), 20-min wait; EDF approx. 17.0

EDF ranges from approx. 0.7 to  approx. 4.5 for typical commuters, and up to approx. 17 in worst-case documented stations.

- EDF > 1 for any commuter waiting longer than the system-average 5 minutes at any station at or above the mean concentration. This is math from cited numbers, not an assumption.
- The decision flip is robust. Station B (96 μg/m³, 20-min wait) produces more inhaled dose than Station A (208 μg/m³, 5-min wait) even at the most conservative bounds, 21.0 μg vs 15.6 μg. This holds across the entire parameter range, not just at the midpoint.
- The 6x behavioral variance is concentration-independent. Two commuters at the exact same station, one waiting 2 min and one waiting 12 min, always differ by 6x in inhaled dose. This result is clean because it's a time ratio only.
- Reported PM2.5 averages systematically underestimate actual inhaled dose for anyone who is not the “average” commuter such as longer wait, more active, or documented high-concentration stations.

## References

- Azad, S., Luglio, D. G., Gordon, T., Thurston, G., & Ghandehari, M. (2023). Particulate matter concentration and composition in the New York City subway system. Atmospheric Pollution Research, 14(6), 101767. https://doi.org/10.1016/j.apr.2023.101767 [PMC10237451]
- Azad, S., Ferrer-Cid, P., & Ghandehari, M. (2024). Exposure to fine particulate matter in the New York City subway system during home-work commute. PLOS ONE, 19(8), e0307096. https://doi.org/10.1371/journal.pone.0307096 [PMC11305539]
- Vilcassim, M. J. R., Thurston, G. D., Peltier, R. E., & Gordon, T. (2014). Black Carbon and Particulate Matter (PM2.5) Concentrations in New York City's Subway Stations. Environmental Science & Technology, 48(24), 14738-14745. https://doi.org/10.1021/es504295h
- Exposure Factors Handbook 2011 Edition (Final Report)