import plotly.graph_objects as go
import plotly.io as pio

from .config import FIG

INK = "#1d1d1b"
INK2 = "#5f5e5a"
MUTED = "#9a9993"
GRID = "#ecebe7"
SURFACE = "#ffffff"

ACCENT = "#2a78d6"
CONTRAST = "#eb6834"
CONTEXT = "#c4c3bd"

SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7", "#e34948"]
DIVERGING = [[0.0, "#e34948"], [0.5, "#f0efec"], [1.0, "#2a78d6"]]
SEQUENTIAL = [[0.0, "#cde2fb"], [0.5, "#3987e5"], [1.0, "#0d366b"]]

FONT = "Inter, 'Helvetica Neue', Arial, sans-serif"


def build_template():
    title = dict(
        font=dict(size=20, color=INK),
        x=0,
        xanchor="left",
        xref="paper",
        y=0.96,
        pad=dict(b=8),
    )
    xaxis = dict(
        showgrid=False,
        showline=True,
        linecolor=GRID,
        ticks="outside",
        tickcolor=GRID,
        ticklen=4,
        title=dict(font=dict(size=12, color=MUTED)),
        zeroline=False,
    )
    yaxis = dict(
        showgrid=True,
        gridcolor=GRID,
        gridwidth=1,
        zeroline=False,
        showline=False,
        ticks="",
        title=dict(font=dict(size=12, color=MUTED)),
    )
    legend = dict(
        orientation="h",
        y=1.02,
        yanchor="bottom",
        x=0,
        xanchor="left",
        bgcolor="rgba(0,0,0,0)",
        font=dict(size=12),
    )
    hoverlabel = dict(
        bgcolor="white",
        bordercolor=GRID,
        font=dict(family=FONT, size=12, color=INK),
    )
    layout = dict(
        font=dict(family=FONT, size=13, color=INK2),
        title=title,
        paper_bgcolor=SURFACE,
        plot_bgcolor=SURFACE,
        colorway=SERIES,
        margin=dict(l=60, r=30, t=95, b=60),
        xaxis=xaxis,
        yaxis=yaxis,
        legend=legend,
        hoverlabel=hoverlabel,
        hovermode="x unified",
    )
    return go.layout.Template(layout=layout)


pio.templates["bart_clean"] = build_template()
pio.templates.default = "bart_clean"


def notebook_mode():
    # plotly_mimetype is drawn by VS Code / JupyterLab itself, notebook_connected loads plotly.js
    # from the CDN in every output, so no figure depends on an earlier cell's output
    pio.renderers.default = "plotly_mimetype+notebook_connected"


def titled(fig, title, subtitle=None):
    text = f"<b>{title}</b>"
    if subtitle is not None:
        text += f"<br><span style='font-size:13px;color:{MUTED}'>{subtitle}</span>"
    fig.update_layout(title_text=text)
    return fig


def note(fig, text, y=-0.16):
    fig.add_annotation(
        text=text,
        xref="paper",
        yref="paper",
        x=0,
        y=y,
        showarrow=False,
        xanchor="left",
        font=dict(size=11, color=MUTED),
    )
    return fig


def vline(fig, x, label, y=1.0, xanchor="left"):
    if xanchor == "left":
        xshift = 4
    else:
        xshift = -4

    fig.add_vline(x=x, line=dict(color=MUTED, width=1, dash="dot"))
    fig.add_annotation(
        x=x,
        y=y,
        yref="paper",
        text=label,
        showarrow=False,
        xanchor=xanchor,
        xshift=xshift,
        font=dict(size=11, color=INK2),
    )
    return fig


def end_label(fig, x, y, text, color=INK, ax=-60, ay=-45):
    fig.add_annotation(
        x=x,
        y=y,
        text=text,
        showarrow=True,
        arrowhead=0,
        arrowcolor=MUTED,
        ax=ax,
        ay=ay,
        font=dict(size=12, color=color),
        align="left",
    )
    return fig


def save(fig, name, width=1000, height=520, scale=2):
    fig.update_layout(width=width, height=height)
    fig.write_html(FIG / f"{name}.html", include_plotlyjs="cdn")

    png_path = FIG / f"{name}.png"
    fig.write_image(png_path, scale=scale)
    return png_path
