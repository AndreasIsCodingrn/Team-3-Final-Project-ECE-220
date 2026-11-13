"""
visualizations package
Owner: Julien Werzowa (Team Member 6)

All the dashboard and report charts live in here, split up by topic:
  charts_rates          - electricity prices, JMEC history, tariff bill curve
  charts_heating        - heating fuel mix and heating costs
  charts_burden         - DOE LEAD energy burden, programs, county maps
  charts_acs            - Census ACS income + heating fuel benchmarks (Cuba village)
  charts_reliability    - SAIDI / SAIFI / CAIDI for JMEC vs NM utilities
  charts_solar_ev_grid  - solar resource, PV estimate, EV charging, generation mix
  charts_summary        - the Cuba gap chart, eRedux cross-check, locator map

Every chart function returns a plotly Figure, so Streamlit just needs:
    st.plotly_chart(fig, use_container_width=True)
"""

from . import (charts_acs, charts_burden, charts_heating, charts_rates, charts_reliability, charts_solar_ev_grid,
               charts_summary, data_loader)

__all__ = ["charts_acs", "charts_burden", "charts_heating", "charts_rates", "charts_reliability",
           "charts_solar_ev_grid", "charts_summary", "data_loader"]
