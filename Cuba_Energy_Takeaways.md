# Cuba, NM Energy Takeaways

**ECE 220 Team 3, Visualizations summary (Julien Werzowa)**
Cuba (ZIP 87013) compared with Sandoval County, Bernalillo County, New Mexico, and the US.
Every number below comes from the team datasets in this repo, and every chart is in the Streamlit dashboard (`streamlit run app.py`).

---

## Bottom line

**Cuba is not in good shape on power, but the problem is not the price per kWh.** Cuba's electricity rate is about average for New Mexico and below the national average. The real problems are:

1. **Reliability.** JMEC, the co-op that serves Cuba, has had the worst or second-worst outage record of all New Mexico utilities in every year from 2013 to 2025.
2. **Heating.** About 64% of Cuba homes heat with wood and another 16% with propane, compared with about 13% combined statewide. These fuels are expensive, labor-intensive, or both.
3. **Affordability for low-income households.** Energy burden is heavily concentrated in the bottom half of Cuba's income distribution. About **48% of Cuba-area households** spend more than 6% of their income on energy, compared with **30% statewide**.

So Cuba is **meaningfully worse off than New Mexico overall** and carries **a large burden on a big share of its population**. The issue is not that power costs more per kWh. It is that the lights go out far more often, heating is expensive, and incomes are low.

---

## Scorecard: Cuba vs. New Mexico vs. US

| Metric | Cuba / JMEC | New Mexico | US | Verdict |
|---|---|---|---|---|
| Residential rate (¢/kWh) | 15.97 (ZIP avg); JMEC 15.36 | 14.20 | 17.44 | Slightly above NM, below US |
| Estimated monthly bill (654 kWh) | $104 | $93 | $151 | About average |
| Outage minutes per customer, excl. major events (SAIDI, 2025) | **472** | 195 (median utility) | n/a | **2.4× worse** |
| Outages per customer per year (SAIFI, 2025) | **3.45** | 1.53 (median utility) | n/a | **2.3× worse** |
| Homes heated with wood | **64%** | 6.3% | 1.5% | **10× NM** |
| Homes heated with propane | 16% | 6.8% | 4.8% | 2.4× NM |
| Average energy burden (household-weighted) | **3.7%** | 2.5% | n/a | **1.5× worse** |
| Households above 6% burden | **48%** (391 of 820) | 30% | n/a | Much worse |
| Solar resource (kWh/m²/day) | 5.5 ("Excellent") | n/a | 4.5 | **22% better than US** |

*Note: Sandoval County's average burden is only 2.0%, one of the lowest in the state. Wealthier Rio Rancho pulls the county average down and hides what is happening in Cuba. County-level numbers should not be used to describe Cuba.*

---

## Key takeaways

### 1. Reliability is Cuba's single worst gap
- JMEC ranked **#1 worst** in New Mexico for normal-day outage minutes in **9 of 13 years** and #2 worst in the other 4.
- Outage minutes more than doubled over the decade, from **215 min (2013) to 472 min (2025)**. 2024 peaked at **1,045 min** on normal days and **1,877 min (~31 hours) including major events**.
- The median NM utility runs about 120–210 min per year. JMEC customers see roughly 2–5× that.
- Customers lose power about **3.5 times a year** versus about 1.5 for a typical NM utility, and restoration takes about 2–3.5 hours per outage in most years.
- *Caveat:* this is co-op-wide data. Cuba sits at the rural end of JMEC's system, so its local numbers could be equal or worse.

### 2. Heating is the hidden affordability problem
- Two-thirds of homes burn wood. The wood-heat burden scenarios leave out the cost of firewood, so **real burdens for wood-heated homes are understated**.
- Cuba is the coldest place in the comparison (about 6,485 heating degree days vs. about 4,500 in Rio Rancho), so **every heating system costs more to run in Cuba**.
- Propane heating costs about **$2,707/yr**, versus **$1,486/yr** for a cold-climate heat pump, a saving of about **$1,221/yr**.
- A lowest-income (0–30% AMI) propane-heated household is at about **45% energy burden**. Even a median-income Cuba propane household is at about **13%**, more than twice the 6% "high burden" line.

### 3. Burden is driven by low incomes, not by abnormally high bills
- Within the same income bracket, Cuba households look similar to the rest of NM (0–30% AMI: 18% in Cuba vs. 20% statewide).
- Cuba simply has far more households in those brackets: 48% are at or below 60% AMI, versus 30% statewide.
- Middle-income Cuba households pay somewhat more for energy than their state peers ($2,150–2,550 vs. $1,900–2,200 per year), which pushes the 30–60% AMI bracket to **9.3% burden vs. 7.0% statewide**.

### 4. Existing assistance programs help but don't solve it
- Stacking weatherization, NM Solar for All, and LIHEAP saves an eligible household about **$680/yr** on average.
- It cuts the lowest bracket from 18% to 11%, and the 30–60% bracket from 9.3% to 6.4%.
- **No Cuba household is moved below the 6% line.** All 391 high-burden households stay high-burden. Statewide, the same programs cut high-burden households by more than half.
- LIHEAP is a one-time credit, not a permanent fix.

### 5. Rates are climbing
- JMEC's average residential price rose **17% from 2015 to 2025** (13.5¢ to 15.8¢/kWh).
- The scheduled 2029 tariff raises a typical 654 kWh bill from about **$121 to $141 per month** (+$21, before power-cost adjustments).
- Under the rate-case phases, the lowest-income wood-heated household goes from 15% to 19% burden.

### 6. Solar is Cuba's biggest untapped asset
- Cuba's solar resource is rated "Excellent" (5.5 kWh/m²/day, 22% above the US average).
- A 6 kW rooftop system should produce about **10,500 kWh/yr**, worth about **$1,520/yr** at JMEC's rate. That is more than a typical household's yearly use (about 7,850 kWh).
- *eRedux's figure of 2,385 kWh/yr is wrong; it implies an unrealistic 4.5% capacity factor.*
- Sandoval County's in-county generation is already 100% solar and wind (470,000 MWh in 2024), though in-county generation is not the same as power delivered to Cuba.

### 7. EV charging is not a priority gap
Cuba has 4–6 DC fast-charging ports on US 550 (the two sources disagree). Nearby Jemez Springs has 11 ports, and Rio Rancho has 6. Public fast charging (about 15.8¢/mile) also costs more than gas (about 14.2¢/mile), so EV access matters less than the items above for Cuba residents right now.

---

## Where government initiatives should focus (in priority order)

| # | Focus | Why | Programs / funding |
|---|---|---|---|
| 1 | **Grid reliability and resilience on JMEC's Cuba lines**: feeder hardening, sectionalizing and automation, vegetation and wildfire work, faster restoration | Worst outage record in NM for over a decade, and getting worse | USDA Rural Development Electric Programs (loans and grants), NM PRC oversight of JMEC reliability, DOE grid-resilience grants |
| 2 | **Solar + battery backup for critical loads** (clinic, schools, water and wastewater, emergency services, senior housing) | Addresses both reliability and cost, and uses Cuba's excellent sun | USDA RD, NM ECMD, NM Solar for All, federal clean-energy grants |
| 3 | **Weatherization targeted at wood- and propane-heated homes** | Heating is the largest cost driver, and it is a cold climate | DOE Weatherization Assistance Program (NM Energy$mart), NM ECMD |
| 4 | **Propane-to-heat-pump conversions** for low-income homes | About $1,200/yr saved per home; propane homes carry the worst burdens (13–45%) | JMEC rebates, NM ECMD, federal home-electrification rebates; pair with weatherization first |
| 5 | **Low-income rate protection before the 2029 increase**: a low-income tariff or discount, and expanded LIHEAP outreach | Existing programs leave all 391 high-burden households above 6% | NM PRC (JMEC rate cases), LIHEAP, NM Solar for All / community solar |
| 6 | **Residential and community solar** for low-income households | A 6 kW system could cover a typical home's yearly use | NM Solar for All, community solar subscriptions through JMEC |

**Recommended order:** reliability and critical-load backup first, because they affect everyone. Then attack heating costs for the low-income majority. Then lock in rate protection before the 2029 tariff takes effect.

---

## Limits of this analysis
- Reliability data covers all of JMEC's territory, not Cuba specifically.
- Burden data is for Census Tract 109 (820 households), which approximates the Cuba area.
- Heating costs are eRedux model estimates for a 2,000 sq ft home. Cuba homes may be smaller.
- Firewood costs are excluded, so wood-heat burdens are understated.
- Cuba's heating-fuel shares come from an ACS sample of only 1,586 housing units and should be checked against the margin of error.
- ACS income and heating data (Census tables B19013 and B25040) and the NREL PVWatts run are still pending from teammates; the eRedux values used here should be replaced once those arrive.
- The 87013 rate on eRedux is an unweighted average of 3 utilities. JMEC's actual rate (15.36¢) is the better number for most residents.
- Impacts are presented as estimated risks, not measured effects on specific households.
