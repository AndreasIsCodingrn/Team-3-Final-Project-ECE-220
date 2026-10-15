# Project Proposal Plan (TEAM 3\) 

## Team Members: Julien Werzowa, Jadon Giron, Michael Nusbietel, Christian Coppedge, Lenny Graham, Andreas Chacon

# Project Abstract 

Reliable, affordable electricity matters everywhere, but in rural communities like Cuba, New Mexico, energy costs and limited infrastructure can be a huge cost and burden to households. This project aims to pinpoint where Cuba’s main issues are in energy affordability and access, and to point out key State and local investments that would have the largest impact.  
Our approach is to benchmark Cuba relative to other key areas to gain an understanding of where it is falling short compared to expectations for the county, state, and potentially even federally. Using zip code-level data from eRedux, which aggregates public datasets from the EIA, Census Bureau, DOE, EPA, and NREL, we will compare Cuba’s zip code (87013) against nearby Sandoval County, Bernalillo County, and then New Mexico as a whole, with potential national averages as well. The comparison will cover residential electricity rates, household heating fuel mix, energy burden, and solar resource potential. To have even more reliability, we will use the EIA’s annual utility reliability data (SAIDI/SAIFI) to compare Jemez Mountains Electric Cooperative, which serves Cuba, relative to other New Mexico utilities. The county and state numbers set a baseline for where Cuba should be, and the gaps show where residents' needs are not being met.  
Using Python, GitHub, and Streamlit, we will clean and process this data into a usable dataset and produce an interactive dashboard showing side-by-side geographic comparisons, affordability metrics, and reliability trends. From there, we will match each identified gap to practical options, such as rooftop solar with storage, weatherization, heating electrification, and backup power for critical loads, and identify local, state, and federal programs that could help fund them.  
We will do our best to recognize the limits of our data and other constraints. Some metrics, like energy burden and generation mix, are only available at the county or regional level, and reliability data is reported for the whole cooperative rather than for Cuba alone. Because this is based primarily on online government and utility sources rather than survey data, we will present probable impacts as estimated risks rather than known effects on the members of the city. The end goal is a short, evidence-based list of priorities showing where investment could make the biggest difference for Cuba residents.

# **Proposed datasets and source links:** 

## Primary data

- eRedux: zip code (87013), county, and state energy profiles; used for initial benchmarking. Third-party aggregator of the federal sources below; figures verified against originals. [https\://eredux.com/](https://eredux.com/)  
- U.S. EIA Form EIA-861: utility-level reliability (SAIDI/SAIFI), customer counts, revenues, sales, and average rates. [https\://www\.eia.gov/electricity/data/eia861/](https://www.eia.gov/electricity/data/eia861/)  
- U.S. Census Bureau, American Community Survey (5-year): household income (Table B19013) and home heating fuel (Table B25040) by ZCTA, county, and state. [https\://data.census.gov/](https://data.census.gov/)  
- U.S. DOE Low-Income Energy Affordability Data (LEAD): energy burden and energy costs by census tract, county, and state. [https\://www\.energy.gov/cmei/scep/low-income-energy-affordability-data-lead-tool](https://www.energy.gov/cmei/scep/low-income-energy-affordability-data-lead-tool) (raw data: [https\://data.openei.org/submissions/6219](https://data.openei.org/submissions/6219))  
- OpenEI U.S. Utility Rate Database: residential rate structures by utility. [https\://openei.org/wiki/Utility\_Rate\_Database](https://openei.org/wiki/Utility_Rate_Database)  
- NREL National Solar Radiation Database / Solar Resource API: solar resource potential by location. [https\://developer.nrel.gov/docs/solar/solar-resource-v1/](https://developer.nrel.gov/docs/solar/solar-resource-v1/)  
- NREL Alternative Fuels Station Locator: EV charging station locations. [https\://afdc.energy.gov/stations](https://afdc.energy.gov/stations)  
- U.S. EPA eGRID: electricity generation mix and emissions by grid subregion. [https\://www\.epa.gov/egrid](https://www.epa.gov/egrid)

Utility and regulatory

- Jemez Mountains Electric Cooperative: service territory, published rates, and programs. [https\://www\.jemezcoop.org/](https://www.jemezcoop.org/)  
- New Mexico Public Regulation Commission: JMEC annual reports and rate filings. [https\://www\.prc.nm.gov/?p=15421](https://www.prc.nm.gov/?p=15421)

Programs and funding

- NM Energy Conservation and Management Division: state energy programs. [https\://www\.emnrd.nm.gov/ecmd/](https://www.emnrd.nm.gov/ecmd/)  
- USDA Rural Development Electric Programs: rural infrastructure assistance. [https\://www\.rd.usda.gov/programs-services/electric-programs](https://www.rd.usda.gov/programs-services/electric-programs)  
- U.S. DOE Weatherization Assistance Program: home energy efficiency for low-income households. [https\://www\.energy.gov/cmei/scep/wap/weatherization-assistance-program-resource-hub](https://www.energy.gov/cmei/scep/wap/weatherization-assistance-program-resource-hub)

# 

# **Team Contributions:**

Work is split so each member owns one data source end to end (research, justification,  download, and cleaning) plus one shared part of the project. Everyone writes the report section and presentation slides for their own data, commits through their own GitHub branch, and speaks during the final video. Roles and individual contributions will also be documented in the  README of the GitHub repository.

| Member  | Data source owned  | Shared responsibility  | Report / final   deliverables |
| :---: | ----- | ----- | ----- |
| Team Member 1   **Jadon Giron** | EIA-861 reliability data  (SAIDI/SAIFI) for JMEC  and other NM utilities | GitHub workflow: repo setup, branch rules, pull request reviews, merges, and README with team roles | Introduction and  background section; repo documentation |
| Team   Member 2 **Mike**  | EIA-861 rates and sales;  OpenEI Utility Rate   Database | Data pipeline: shared data schema,  merging all sources into one master  dataset, data dictionary | Data and   methodology section |
| Team   Member 3 **Lenny Graham** | Census ACS income   (B19013) and heating fuel  (B25040) by ZIP, county,  and state | Benchmarking analysis: computing  Cuba vs. county vs. state gaps and  ranking them | Results section; final report editor |
| Team   Member 4 **Andreas Chacon** | DOE LEAD energy burden  (tract and county) | Programs and recommendations:  matching each gap to fixes and NM  ECMD, USDA RD, and DOE funding  programs | Recommendations  and limitations   sections |
| Team   Member 5: **Christian Coppedge** | NREL solar resource, AFDC  EV stations, EPA eGRID  generation mix | Streamlit application: layout,   interactivity, integrating charts, and  deployment | Dashboard   walkthrough; video  recording and   editing |
| Team Member 6: **Julien Werzowa** | eRedux ZIP/county/state  profiles; cross-checking  eRedux against federal  originals | Visualizations: comparison charts,  maps, and trend plots used in the  dashboard and report | Figures;   presentation slide  design |

# Deliverables

**Project proposal (this document, submitted as PDF)**: abstract with dataset links and expected team contributions.   
**Final submission**: 

- GitHub repository with a reproducible dataset and documented code,   
- a working Streamlit dashboard,   
- a project report,   
- a PowerPoint presentation,   
- and a video explaining the project.

