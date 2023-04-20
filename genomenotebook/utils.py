# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/01_utils.ipynb.

# %% auto 0
__all__ = ['Y_RANGE', 'gene_y_range', 'create_genome_browser_plot', 'get_genome_annotations', 'extract_attribute',
           'get_genes_from_annotation', 'get_y_range', 'get_all_glyphs', 'rect_patch', 'arrow_patch', 'get_arrow_patch',
           'get_gene_patches']

# %% ../nbs/01_utils.ipynb 4
import gffpandas.gffpandas as gffpd
import numpy as np

from bokeh.plotting import figure
from bokeh.models.tools import BoxZoomTool
from bokeh.models import HoverTool, NumeralTickFormatter, LabelSet
from bokeh.models.glyphs import Patches
from bokeh.models import (
    CustomJS,
    Range1d,
    ColumnDataSource,
)

# %% ../nbs/01_utils.ipynb 5
def create_genome_browser_plot(glyphSource, x_range, **kwargs):
    plot_height = kwargs.get("plot_height", 150)
    label_angle = kwargs.get("label_angle", 45)
    text_font_size = kwargs.get("text_font_size", "10pt")
    output_backend = kwargs.get("output_backend", "webgl")
    
    y_min, y_max = get_y_range()
    p_annot = figure(
        tools = "xwheel_zoom,xpan,save",
        active_scroll = "xwheel_zoom",
        height = plot_height,
        x_range = x_range,
        y_range = Range1d(y_min, y_max),
        output_backend=output_backend,
    )
    # Add tool
    p_annot.add_tools(BoxZoomTool(dimensions="width"))

    #p_annot.sizing_mode = "stretch_both"

    # Format x axis values
    p_annot.xaxis[0].formatter = NumeralTickFormatter(format="0,0")
    # Hide grid
    p_annot.xgrid.visible = False
    p_annot.ygrid.visible = False
    # Hide axis
    p_annot.yaxis.visible = False
    glyph = p_annot.add_glyph(
        glyphSource, Patches(xs="xs", ys="ys", fill_color="color")
    )
    # gene labels in the annotation track
    # This seems to be necessary to show the labels
    p_annot.scatter(x="pos", y=0, size=0, source=glyphSource)
    labels = LabelSet(
        x="pos",
        y=-0.9,
        text="names",
        level="glyph",
        angle=label_angle,
        text_font_size=text_font_size,
        x_offset=-5,
        y_offset=0,
        source=glyphSource,
        text_align='left',
    )

    p_annot.add_layout(labels)
    p_annot.add_tools(
        HoverTool(
            renderers=[glyph],
            tooltips=[("locus_tag", "@locus_tag"), ("gene", "@gene"), ("product", "@product")],
        )
    )
    return p_annot

# %% ../nbs/01_utils.ipynb 6
def get_genome_annotations(gff_path: str, bounds=None):
    annotation = gffpd.read_gff3(gff_path)
    annotation = annotation.attributes_to_columns()
    if bounds:
        annotation = annotation.loc[(annotation.start<bounds[1]) & (annotation.end>bounds[0])]

    annotation.loc[:, "left"] = annotation[["start"]].values
    annotation.loc[:, "right"] = annotation[["end"]].values
    return annotation

# %% ../nbs/01_utils.ipynb 7
def get_genome_annotations(gff_path: str, bounds=None):
    annotation = gffpd.read_gff3(gff_path)
    annotation = annotation.df
    if bounds:
        annotation = annotation.loc[(annotation.start<bounds[1]) & (annotation.end>bounds[0])]

    annotation.loc[:, "left"] = annotation[["start"]].values
    annotation.loc[:, "right"] = annotation[["end"]].values
    return annotation

# %% ../nbs/01_utils.ipynb 8
from .js_callback_code import get_example_data_dir
import os

# %% ../nbs/01_utils.ipynb 10
import re

# %% ../nbs/01_utils.ipynb 11
def extract_attribute(input_str:str, #attribute string to parse
                      attr_name:str, #name of the attribute to extract
                     ) -> dict:
    
    pattern = f"[{attr_name[0].lower()}{attr_name[0].upper()}]{attr_name[1:]}=(?P<{attr_name}>[^;]+)"
    match = re.search(pattern, input_str)
    if match:
        return match.groupdict()[attr_name]
    else:
        return None

# %% ../nbs/01_utils.ipynb 14
def get_genes_from_annotation(annotation):

    genes = annotation[
        annotation.type.isin(["CDS", "repeat_region", "ncRNA", "rRNA", "tRNA"])
    ].copy()

    genes.loc[genes["strand"] == "+", "start"] = genes.loc[
        genes["strand"] == "+", "left"
    ].values

    genes.loc[genes["strand"] == "+", "end"] = genes.loc[
        genes["strand"] == "+", "right"
    ].values

    genes.loc[genes["strand"] == "-", "start"] = genes.loc[
        genes["strand"] == "-", "right"
    ].values

    genes.loc[genes["strand"] == "-", "end"] = genes.loc[
        genes["strand"] == "-", "left"
    ].values
    
    genes['gene'] = genes.attributes.apply(extract_attribute,attr_name='gene')
    genes['locus_tag'] = genes.attributes.apply(extract_attribute,attr_name='locus_tag')
    genes['gene_or_locus'] = genes['gene'].fillna(genes['locus_tag'])
    genes['product'] = genes.attributes.apply(extract_attribute,attr_name='product')
    genes.loc[genes["type"] == "repeat_region", "gene"] = "REP"
    
    return genes

# %% ../nbs/01_utils.ipynb 17
Y_RANGE = (-2, 2)
def get_y_range() -> tuple:
    """Accessor that returns the Y range for the genome browser plot
    """
    return Y_RANGE


def get_all_glyphs(genes,bounds:tuple):
    all_glyphs=get_gene_patches(genes, bounds[0], bounds[1])

    ks=list(all_glyphs.keys())
    ref_list_ix=ks.index('xs')
    # Sort all the lists in the dictionary based on the values of the reference list
    sorted_lists = sorted(zip(*[all_glyphs[k] for k in ks]), key= lambda x: x[ref_list_ix][0])

    # Convert the sorted tuples back into separate lists
    unzipped_lists = zip(*sorted_lists)

    # Create a new dictionary with the same keys as the original dictionary, but with the sorted lists as values
    all_glyphs = {k: list(t) for k, t in zip(ks, unzipped_lists)}
    
    return all_glyphs

# %% ../nbs/01_utils.ipynb 18
def rect_patch(genes_region):
    y_min, y_max = gene_y_range
    xs = list(
        zip(
            genes_region.start.values,
            genes_region.start.values,
            genes_region.end.values,
            genes_region.end.values,
        )
    )
    xs = [np.array(x) for x in xs]
    ys = [np.array([y_min, y_max, y_max, y_min]) for i in range(genes_region.shape[0])]
    genes_mid = genes_region.left + (genes_region.right - genes_region.left) / 2
    pos = list(genes_mid.values)
    names = list(genes_region.gene.values)
    product = list(genes_region["product"].values)
    color = ["grey"] * genes_region.shape[0]
    return dict(
        xs=xs,
        ys=ys,
        pos=pos,
        names=[""] * genes_region.shape[0],
        gene=list(genes_region.gene.values),
        locus_tag=list(genes_region.locus_tag.values),
        hover_names=names,
        product=product,
        color=color,
    )

# %% ../nbs/01_utils.ipynb 19
def arrow_patch(genes_region):
    arr_plus = get_arrow_patch(genes_region[genes_region["strand"] == "+"], "+")
    arr_minus = get_arrow_patch(genes_region[genes_region["strand"] == "-"], "-")
    return dict([(k, arr_plus[k] + arr_minus[k]) for k in arr_plus.keys()])

# %% ../nbs/01_utils.ipynb 20
gene_y_range = (-1.5, -1)

def get_arrow_patch(genes_region, ori="+"):
    y_min, y_max = gene_y_range
    y_min = y_min 
    if ori == "+":
        xs = list(
            zip(
                genes_region.start.values,
                genes_region.start.values,
                np.maximum(genes_region.start.values, genes_region.end.values - 100),
                genes_region.end.values,
                np.maximum(genes_region.start.values, genes_region.end.values - 100),
            )
        )
        color = ["orange"] * genes_region.shape[0]
    elif ori == "-":
        xs = list(
            zip(
                genes_region.start.values,
                genes_region.start.values,
                np.minimum(genes_region.start.values, genes_region.end.values + 100),
                genes_region.end.values,
                np.minimum(genes_region.start.values, genes_region.end.values + 100),
            )
        )
        color = ["purple"] * genes_region.shape[0]

    ys = [
        np.array([y_min, y_max, y_max, (y_max + y_min) / 2, y_min])
        for i in range(genes_region.shape[0])
    ]
    genes_mid = (genes_region.right + genes_region.left) / 2
    pos = list(genes_mid.values)
    return dict(
        xs=xs,
        ys=ys,
        pos=pos,
        names=list(genes_region.gene_or_locus.values),
        gene=list(genes_region.gene.values),
        locus_tag=list(genes_region.locus_tag.values),
        hover_names=list(genes_region.gene_or_locus.values),
        product=list(genes_region["product"].values),
        color=color,
    )

# %% ../nbs/01_utils.ipynb 21
def get_gene_patches(genes, left, right):
    genes_region = genes[
        (genes["right"] > left)
        & (genes["left"] < right)
        & (genes["type"] != "repeat_region")
    ]
    arr = arrow_patch(genes_region)
    # repeat_region
    rep_region = genes[
        (genes["right"] > left)
        & (genes["left"] < right)
        & (genes["type"] == "repeat_region")
    ]
    rect = rect_patch(rep_region)

    # concatenate patches
    res = dict([(k, arr[k] + rect[k]) for k in arr.keys()])
    return res