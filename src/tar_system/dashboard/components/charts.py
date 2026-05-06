"""Dashboard chart helpers."""

from __future__ import annotations

import pandas as pd


def line_chart(st: object, values: list[float], title: str) -> None:
    st.subheader(title)
    if values:
        st.line_chart(pd.DataFrame({"value": values}))
    else:
        st.write("No chart data available.")
