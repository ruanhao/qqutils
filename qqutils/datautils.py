from typing import List, Tuple, Dict, Any
import logging
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.axes._axes import Axes
import numpy as np
from .osutils import temp_file
from .dateutils import timestamp_millis
import os


logger = logging.getLogger(__name__)


def create_figure() -> Tuple[Figure, Axes]:
    import seaborn as sns
    sns.set_theme()

    fig = plt.figure(num=timestamp_millis(), clear=True)
    ax = fig.add_subplot()
    return fig, ax


def save_figure(fig: Figure, filepath: str = None) -> None:
    """Save the current figure of the matplotlib plot."""
    if filepath:
        if not os.path.exists(os.path.dirname(filepath)):
            base_filename = os.path.basename(filepath)
            filepath = temp_file(base_filename)
    else:
        filepath = temp_file(f"fig_{fig.number}.png")

    fig.savefig(filepath)
    logger.info(f"Saved plot to: {filepath}")
    return filepath


# ref: https://matplotlib.org/stable/api/_as_gen/matplotlib.lines.Line2D
def draw_single_line(
        ydata: List[float],
        xdata: List[float] = None,
        title: str = None,
        ls: str = '-',
        color: str = 'b',
        width: float = 1.0,
        marker: str = None,
        xlabel: str = None,
        ylabel: str = None,
        ylim: Tuple[float, float] = None,
        autofmt_xdate=False,    # Rotate x-axis labels for dates
        fill_between=False,
) -> str:
    """Draw a single line plot of the data using matplotlib. Ruturn the path of the saved plot."""

    if xdata is None:
        xdata = list(range(len(ydata)))
    assert len(xdata) == len(ydata), "xdata and ydata must have the same length."
    ypoints = np.array(ydata)
    xpoints = np.array(xdata)
    fig, ax = create_figure()
    ax.plot(xpoints, ypoints, ls=ls, c=color, linewidth=width, marker=marker)
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_ylim(ylim)
    if fill_between:
        ax.fill_between(xdata, ydata, alpha=0.3, color='blue')
    if autofmt_xdate:
        fig.autofmt_xdate()
    return save_figure(fig)


# ref: https://matplotlib.org/stable/gallery/lines_bars_and_markers/line_demo_dash_control.html#sphx-glr-gallery-lines-bars-and-markers-line-demo-dash-control-py
def draw_multi_lines(
        ydatas: List[Dict[str, Any]],  # List of dictionaries with keys: ydata, xdata, ls, color, width, marker, label
        xdata: List[float] = None,
        title: str = None,
        xlabel: str = None,
        ylabel: str = None,
        ylim: Tuple[float, float] = None,
        only_markers: bool = False,
        filepath: str = None,
) -> str:
    max_length = max([len(yd.get('ydata', [])) for yd in ydatas])
    if xdata is None:
        xdata = list(range(max_length))

    assert len(xdata) == max_length, "xdata and ydata must have the same length."
    fig, ax = create_figure()
    xpoints = np.array(xdata)
    for ydata_info in ydatas:
        ydata = ydata_info.get('ydata', [])
        ypoints = np.array(ydata)
        ls = "None" if only_markers else (ydata_info.get('ls') or ydata_info.get('linestyle'))
        color = ydata_info.get('color')
        width = ydata_info.get('width')
        marker = ydata_info.get('marker', None)
        ax.plot(xpoints, ypoints, ls=ls, c=color, linewidth=width, marker=marker)

    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_ylim(ylim)
    ax.legend([yd.get('label') for yd in ydatas])
    return save_figure(fig, filepath)


# ref: https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.bar.html
def draw_single_bar(
        ydata: List[float],
        xdata: List[float] = None,
        title: str = None,
        color: str = 'b',
        width: float = 0.8,
        xlabel: str = None,
        ylabel: str = None,
) -> str:
    """Draw a single bar plot of the data using matplotlib. Ruturn the path of the saved plot."""
    if xdata is None:
        xdata = list(range(len(ydata)))
    assert len(xdata) == len(ydata), "xdata and ydata must have the same length."
    ypoints = np.array(ydata)
    xpoints = np.array(xdata)
    fig, ax = create_figure()
    ax.bar(xpoints, ypoints, color=color, width=width)
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    return save_figure(fig)


# ref: https://matplotlib.org/stable/gallery/lines_bars_and_markers/barchart.html#sphx-glr-gallery-lines-bars-and-markers-barchart-py
def draw_grouped_bar(
        groups: List[str],
        values: Dict[str, List[float]],
        title: str = None,
        ylabel: str = None,
        ylimit: Tuple[float, float] = None,
        width = 0.25,
) -> str:
    x = np.arange(len(groups))
    multiplier = 0.5 if len(values) % 2 == 0 else 0

    fig, ax = create_figure()

    for attribute, value in values.items():
        offset = width * multiplier
        rects = ax.bar(x + offset, value, width, label=attribute)
        multiplier += 1
        ax.bar_label(rects, padding=5)

    ax.set_title(title)
    ax.set_ylabel(ylabel)
    ax.set_xticks(x + width, groups)
    ax.legend(loc='upper left', ncol=len(values))
    if ylimit:
        ax.set_ylim(ylimit)
    else:
        max_y = max([max(v) for v in values.values()])
        ax.set_ylim(0, max_y * (2 - 0.618))
    return save_figure(fig)
