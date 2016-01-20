__doc__ = """ Plotting submodule for epistasis models."""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib
from scipy.stats import norm as scipy_norm

from seqspace.errors import BaseErrorMap

# ---------------------------------------------------
# Epistasis Graphing
# ---------------------------------------------------


def magnitude_vs_order(model, keep_sign=False, 
        marker="o", 
        color="b",
        linestyle="None",
        xlabel="Order", 
        ylabel="Magnitude", 
        title="", 
        figsize=(6,4),
        **kwargs):
    """
        Generate a plot of magnitude versus order.
    
    """    
    orders = range(1, model.length+1)
    magnitudes = []
    for i in orders:
        coeffs = np.array(list(model.Interactions.get_order(i).values()))
        
        # Do we care about signs? 
        if keep_sign is False:
            coeffs = abs(coeffs)
        
        # Add magnitudes
        magnitudes.append(np.mean(coeffs))
    
    # Initialize the figure and axis
    fig, ax = plt.subplots(figsize=figsize)
    
    # Create plot
    ax.plot(orders, magnitudes, marker=marker, color=color, linestyle=linestyle, **kwargs)
    
    # Steal the max bound, cause matplotlib does a great job of picking good axis
    ylimits = max(list(ax.get_ylim()))
    # Make y limits symmetric
    ax.axis([orders[0], orders[-1], -ylimits, ylimits])
    
    # Add a line at zero if keeping sign
    if keep_sign:
        ax.hlines(0, orders[0], orders[-1], linestyle="--")
    
    # ---------------------------------
    # Plot styling
    # ---------------------------------
    
    extra_limit_frac = 0.05
    spine_widths = 1.35
    line_widths = 1.5
    
    # Get current axis limits
    xlimits = list(ax.get_xlim())
    ylimits = list(ax.get_ylim())
    xticks = list(ax.get_xticks())
    yticks = list(ax.get_yticks())

    # Extend the graph by 5 percent on all sides
    xextra = extra_limit_frac*(xlimits[1] - xlimits[0])
    yextra = extra_limit_frac*(ylimits[1] - ylimits[0])

    # set ticks and tick labels
    ax.set_xlim(xlimits[0] - xextra, xlimits[1] + xextra)
    ax.set_ylim(ylimits[0] - yextra, ylimits[1] + yextra)

    # Remove right and top spines
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)

    # Set the bounds for visible axes
    ax.spines['bottom'].set_bounds(xlimits[0], xlimits[1])
    ax.spines['left'].set_bounds(ylimits[0], ylimits[1])

    # Thicken the spines
    ax.spines['bottom'].set_linewidth(spine_widths)
    ax.spines['left'].set_linewidth(spine_widths)

    # Only show ticks on the left and bottom spines
    ax.yaxis.set_ticks_position('left')
    ax.xaxis.set_ticks_position('bottom')

    # Make ticks face outward and thicken them
    ax.tick_params(direction='out', width=spine_widths)

    if xticks[-1] > xlimits[1]:
        xticks = xticks[:-1]
       
    if yticks[-1] > ylimits[1]:
        yticks = yticks[:-1]
    
    ax.set_xticks(xticks)
    ax.set_yticks(yticks)



def bar_with_xbox(model,
                  order_colors=("red","orange","green","purple","DeepSkyBlue","yellow","pink"),
                  significance="bon",
                  significance_cutoff=0.05,
                  sigmas=2,
                  y_scalar=1.5,
                  y_axis_name="interaction",
                  figsize=(8,10),
                  height_ratio=12,
                  star_cutoffs=(0.05,0.01,0.001),
                  star_spacer=0.0075,
                  ybounds=None,
                  bar_borders=True):
    """
    Create a barplot with the values from model, drawing the x-axis as a grid of
    boxes indicating the coordinate of the epistatic parameter. Should automatically
    generate an almost publication-quality figure.

    input:
        model: epistasis model
        order_colors: list/tuple of colors for each order (rgb,html string-like)
        significance: how to treat signifiance.  should be:
                      "bon" -> Bonferroni corrected p-values (default)
                      "p" -> raw p-values
                      None -> ignore significance
        significance_cutoff: value above which to consider a term significant
        sigmas: number of sigmas to show for each error bar
        y_scalar: how much to scale the y-axis above and beyond y-max
        y_axis_name: what to put on the y-axis of the barplot

        figsize: tuple of figure width,height
        height_ratio: how much to scale barplot relative to xbox
        star_cutoffs: signifiance cutoffs for star stack.  should go from highest
                      p to lowest p (least to most significant)
        star_spacer: constant that scales how closely stacked stars are from one
                     another

    output:
        pretty-graph objects fig and ax_array (ax_array has two entries for top
        and bottom panels)
    """
    # Sanity check on the errors
    if sigmas == 0:
        significance = None
    elif significance == None:
        sigmas = 0

    # Grab the fit values and labels, tossing 0th-order term
    bar_y = model.Interactions.values[1:]
    labels = model.Interactions.labels[1:]

    # Figure out the length of the x-axis and the highest epistasis observed
    num_terms = len(labels)
    highest_order = max([len(l) for l in labels])

    # Figure out how many sites are in the dataset (in case of non-binary system)
    all_sites = []
    for l in labels:
        all_sites.extend(l)
    all_sites = list(dict([(s,[]) for s in all_sites]).keys())
    all_sites.sort()
    num_sites = len(all_sites)

    # Figure out how to color each order
    if order_colors == None:
        order_colors = ["gray" for i in range(highest_order+1)]
    else:
        if len(order_colors) < highest_order:
            err = "order_colors has too few entries (at least {:d} needed)\n".format(highest_order)
            raise ValueError(err)

        # Stick gray in the 0 position for insignificant values
        order_colors = list(order_colors)
        order_colors.insert(0,"gray")

    # ---------------------- #
    # Deal with significance #
    # ---------------------- #
    
    # NEED TO RETURN TO SIGNIFICANCE FUNCTIONS
    
    if sigmas == 0:
        
        significance = None
    
    else:
        
        # If log transformed, need to get raw values for normal distribution
        if model.log_transform:
            
            beta = model.Interactions.Raw.values
            sigma_beta = model.Interactions.Raw.err.upper
            z_score = - abs( (beta - 1)/sigma_beta )
            
        # else, just grab standard values
        else:
            beta = model.Interactions.values
            sigma_beta = model.Interactions.err.upper
            z_score = - abs( (beta)/sigma_beta )

    # straight p-values
    if significance == "p":
        p_values = 2*scipy_norm.cdf( z_score )

    # bonferroni corrected p-values
    elif significance == "bon":
        p_values = 2*scipy_norm.cdf( z_score ) * len(beta)
        
    # ignore p-values and color everything
    elif significance == None:
        p_values = [0 for i in range(len(labels))]
        significance_cutoff = 1.0

    # or die
    else:
        err = "signifiance argument {:s} not recognized\n".format(significance)
        raise ValueError(err)

    # Create color array based on significance
    color_array = np.zeros((len(labels)),dtype=int)
    for i, l in enumerate(labels):
        if p_values[i] < significance_cutoff:
            color_array[i] = len(l) - 1
        else:
            color_array[i] = -1

    # ---------------- #
    # Create the plots #
    # ---------------- #

    # Make a color map
    cmap = matplotlib.colors.ListedColormap(colors=order_colors)
    cmap.set_bad(color='w', alpha=0) # set the 'bad' values (nan) to be white and transparent
    bounds = range(-1,len(order_colors))
    norm = matplotlib.colors.BoundaryNorm(bounds, cmap.N)

    # Create a plot with an upper and lower panel, sharing the x-axis
    fig = plt.figure(figsize=figsize)
    gs = matplotlib.gridspec.GridSpec(2, 1, height_ratios=[height_ratio, 1])
    ax_array = [plt.subplot(gs[0])]
    ax_array.append(plt.subplot(gs[1],sharex=ax_array[0]))

    # ------------------ #
    # Create the barplot #
    # ------------------ #

    # set up bar colors
    colors_for_bar = np.array([matplotlib.colors.colorConverter.to_rgba(order_colors[(i+1)]) for i in color_array])

    # Plot error if sigmas are given.
    if sigmas == 0:
        ax_array[0].bar(range(len(bar_y)), bar_y, width=0.8, color=colors_for_bar, edgecolor="none")
    else:
        
        if model.log_transform:
            upper = BaseErrorMap.transform_upper(sigmas*model.Interactions.Raw.err.upper, model.Interactions.Raw.values)
            lower = BaseErrorMap.transform_lower(sigmas*model.Interactions.Raw.err.lower, model.Interactions.Raw.values)
        else:
            upper = sigmas * model.Interactions.err.upper
            lower = sigmas * model.Interactions.err.lower
        
        yerr = [lower[1:], upper[1:]]
        ax_array[0].bar(range(len(bar_y)), bar_y, width=0.8, yerr=yerr, color=colors_for_bar,
                        error_kw={"ecolor":"black"},
                        edgecolor="none",
                        linewidth=2)
                        
    ax_array[0].hlines(0, 0, len(model.Interactions.values)-1, linewidth=1, linestyle="--")

    # Label barplot y-axis
    ax_array[0].set_ylabel(y_axis_name, fontsize=14)

    # Set barplot y-scale
    if ybounds is None:
        ymin = -y_scalar*max(abs(bar_y))
        ymax =  y_scalar*max(abs(bar_y))
    else:
        ymin = ybounds[0]
        ymax = ybounds[1]

    # Make axes pretty pretty
    ax_array[0].axis([-1, len(bar_y) + 1, ymin, ymax])
    ax_array[0].set_frame_on(False) #axis("off")
    ax_array[0].get_xaxis().set_visible(False)
    ax_array[0].get_yaxis().tick_left()
    ax_array[0].get_yaxis().set_tick_params(direction='out')
    ax_array[0].add_artist(matplotlib.lines.Line2D((-1,-1), (ax_array[0].get_yticks()[1], ax_array[0].get_yticks()[-2]), color='black', linewidth=1))

    # add vertical lines between order breaks
    previous_order = 1
    for i in range(len(labels)):
        if len(labels[i]) != previous_order:
            ax_array[0].add_artist(matplotlib.lines.Line2D((i,i),
                                                           (ymin,ymax),
                                                           color="black",
                                                           linestyle="--"))
            previous_order = len(labels[i])

    # ------------------------- #
    # Create significance stars #
    # ------------------------- #
    if sigmas != 0:
        min_offset = star_spacer*(ymax-ymin)
        for i in range(len(p_values)):

            star_counter = 0
            for j in range(len(star_cutoffs)):
                if p_values[i] < star_cutoffs[j]:
                    star_counter += 1
                else:
                    break

            for j in range(star_counter):
                ax_array[0].text(x=(i+0.5),y=ymin+(j*min_offset),s="*")

    # --------------------------- #
    # Create the box-array x-axis #
    # --------------------------- #

    # make an empty data set
    data = np.ones((num_sites,num_terms),dtype=int)*np.nan

    # Make entries corresponding to each coordinate 1
    for i, l in enumerate(labels):
        for j in l:
            data[(j-1),i] = color_array[i]

    # draw the grid
    for i in range(num_terms + 1):
        ax_array[1].add_artist(matplotlib.lines.Line2D((i,i),
                                                       (0,num_sites),
                                                       color="black"))

    for i in range(num_sites + 1):
        ax_array[1].add_artist(matplotlib.lines.Line2D((0,num_terms),
                                                       (i,i),
                                                       color="black"))

    # draw the boxes
    ax_array[1].imshow(data, interpolation='nearest',cmap=cmap,norm=norm,
                       extent=[0, num_terms, 0, num_sites], zorder=0)

    # turn off the axis labels
    ax_array[1].set_frame_on(False)
    ax_array[1].axis("off")
    ax_array[1].set_xticklabels([])
    ax_array[1].set_yticklabels([])
    plt.setp([a.get_xticklabels() for a in fig.axes[:-1]], visible=False)

    # Draw the final figure
    fig.tight_layout()

    return fig, ax_array


# -----------------------------
# Useful plots for analyzing data
# from regression data.
# -----------------------------

def correlation(learned, known, title="Known vs. Learned", figsize=[6,6]):
    """ Create a plot showing the learned data vs. known data. """

    fig, ax = plt.subplots(1,1, dpi=300, figsize=figsize)

    ax.plot(known, learned, '.b')
    ax.hold(True)
    x = np.linspace(min(known), max(known), 1000)
    ax.plot(x,x, '-r', linewidth=1)
    ax.set_xlabel("Known", fontsize = 14)
    ax.set_ylabel("Learned", fontsize=14)
    ax.set_title(title, fontsize=14)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.yaxis.set_ticks_position('left')
    ax.xaxis.set_ticks_position('bottom')

    return fig

def residuals(learned, known, title="Residual Plot", figsize=[6,4]):
    """ Generate a residual plot. """
    fig, ax = plt.subplots(1,1, dpi=300, figsize=figsize)

    ax.stem(known, (learned-known), 'b-', markerfmt='.')
    ax.set_title(title, fontsize=20)
    ax.set_xlabel("True")
    ax.set_ylabel("Residuals")

    return fig
