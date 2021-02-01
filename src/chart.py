from src.analyse import Changeset

import numpy as np
import matplotlib
import matplotlib.pyplot as plt

actions = ["Create", "Modify", "Delete"]
enetities = ["Node", "Ref Node", "Way",
    "Relations", "Highway", "Building"]

def heatmap(data, row_labels, col_labels, ax=None,
            cbar_kw={}, cbarlabel="", **kwargs):
    """Generate heatmap based on data and col/row labels
    """
    ax = plt.gca()

    # Plot the heatmap
    im = ax.imshow(data, **kwargs)

    # We want to show all ticks...
    ax.set_xticks(np.arange(data.shape[1]))
    ax.set_yticks(np.arange(data.shape[0]))
    ax.set_xticklabels(col_labels)
    ax.set_yticklabels(row_labels)

    # Turn spines off and create white grid.
    for edge, spine in ax.spines.items():
        spine.set_visible(False)

    ax.set_xticks(np.arange(data.shape[1]+1)-.5, minor=True)
    ax.set_yticks(np.arange(data.shape[0]+1)-.5, minor=True)
    ax.grid(which="minor", color="w", linestyle='-', linewidth=6)
    return im

def annotate_heatmap(im, data=None, valfmt="{x}",
                     textcolors=("black", "white"),
                     threshold=None, **textkw):
    """Annotate the heatmap based on count of
    """
    if not isinstance(data, (list, np.ndarray)):
        data = im.get_array()

    # Normalize the threshold to the images color range.
    if threshold is not None:
        threshold = im.norm(threshold)
    else:
        threshold = im.norm(data.max())/2.

    kw = dict(horizontalalignment="center",
              verticalalignment="center")
    kw.update(textkw)

    if isinstance(valfmt, str):
        valfmt = matplotlib.ticker.StrMethodFormatter(valfmt)

    texts = []
    for i in range(data.shape[0]):
        for j in range(data.shape[1]):
            kw.update(color=textcolors[int(im.norm(data[i, j]) > threshold)])
            text = im.axes.text(j, i, valfmt(data[i, j], None), **kw)
            texts.append(text)
    return texts


def gen_changestat_png(ch: Changeset):
    """Generate png chart of changesets and save it as
    temp file which will be replaced for every file
    """
    changes = np.array([ch.count_nodes, ch.count_ref_nodes,
        ch.count_ways, ch.count_rels, ch.count_highway, ch.count_building])
    fig, ax = plt.subplots()
    im = heatmap(changes.astype(int).transpose(), actions,
        enetities, ax=ax, cmap="YlGn")
    annotate_heatmap(im)
    fig.tight_layout()
    ax.set_title(f"Changes of changeset {ch.id}:")
    fig.savefig("temp.png")
