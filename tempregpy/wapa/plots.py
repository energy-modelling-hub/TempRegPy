import numpy as np
import matplotlib.pyplot as plt
from ..logging_config import *


def plot_dispatch(df_dispatch, df_lmp, unit_name=''):
    fig, ax1 = plt.subplots(nrows=1, ncols=1, figsize=(12, 6), sharex=True)

    # Plot the stacked area chart on the primary y-axis of the first subplot
    df_dispatch.plot.area(ax=ax1, alpha=0.6)

    # Customizations for the primary y-axis
    ax1.set_title(f'Turbine and Bypass Release for {unit_name}', fontsize=15)
    ax1.set_ylabel('Release (CFS)', fontsize=12)

    # Customize the x-ticks for the shared x-axis
    # ax1.set_xticks(np.arange(0, len(df_dispatch.index)))
    # ax1.set_xticklabels(df_dispatch.index)
    xticks = np.arange(0, len(df_dispatch.index), 6)
    ax1.set_xticks(xticks)
    ax1.set_xticklabels(df_dispatch.index[xticks])

    # Grid for better visualization
    ax1.grid(True, linestyle='--', alpha=0.5)

    # Customize the colors for the area plot
    # colors = ['#ff9999', '#66b3ff']
    colors = ['#ff9999', '#66b3ff']
    # Set colors for the area plot
    for i, poly in enumerate(ax1.collections):
        if i < len(colors):
            poly.set_facecolor(colors[i])
            poly.set_edgecolor(colors[i])
            poly.set_alpha(0.6)

    # Calculate the cumulative sum for the upper edges
    cumulative = df_dispatch.cumsum(axis=1)
    for i, color in enumerate(colors):
        ax1.plot(cumulative.index, cumulative.iloc[:, i], color=color, linewidth=2)

    # Create a secondary y-axis for the first subplot
    ax2 = ax1.twinx()

    # Plot df_lmp on the secondary y-axis of the first subplot without generating a legend
    df_lmp.plot(ax=ax2, color='black', linewidth=2, legend=False)

    # Customizations for the secondary y-axis
    ax2.set_ylabel('LMP ($/MWh)', fontsize=12)

    # Combine legends for the first subplot
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left', fontsize=12, title='Categories', title_fontsize='14')

    return fig

def plot_temperature_analysis(df_dispatch, df_t, df_lmp, save_fig=False, fig_name=''):
    # Define the plot with subplots
    fig, (ax1, ax3, ax4) = plt.subplots(nrows=3, ncols=1, figsize=(12, 15), sharex=True)

    # Plot the stacked area chart on the primary y-axis of the first subplot
    df_dispatch.plot.area(ax=ax1, alpha=0.6)

    # Customizations for the primary y-axis
    ax1.set_title('Turbine and Bypass Release', fontsize=15)
    ax1.set_ylabel('CFS', fontsize=12)

    # Customize the x-ticks for the shared x-axis
    ax1.set_xticks(np.arange(0, len(df_dispatch.index)))
    ax1.set_xticklabels(df_dispatch.index)

    # Grid for better visualization
    ax1.grid(True, linestyle='--', alpha=0.5)

    # Customize the colors for the area plot
    # colors = ['#ff9999', '#66b3ff']
    colors = ['#ff9999', '#66b3ff']
    for i, patch in enumerate(ax1.get_children()[:2]):
        patch.set_color(colors[i])

    # Create a secondary y-axis for the first subplot
    ax2 = ax1.twinx()

    # Plot df_lmp on the secondary y-axis of the first subplot without generating a legend
    df_lmp.plot(ax=ax2, color='black', linewidth=2, legend=False)

    # Customizations for the secondary y-axis
    ax2.set_ylabel('LMP ($/MWh)', fontsize=12)

    # Combine legends for the first subplot
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left', fontsize=12, title='Categories', title_fontsize='14')

    # Plot df_t on the second subplot with specific colors for T_RM61 and T_RM61_max
    df_t['T_RM61'].plot(ax=ax3, linewidth=2, color='black', label='T_RM61')
    df_t['T_RM61_max'].plot(ax=ax3, linewidth=2, linestyle='--', color='red', label='T_RM61_max')
    df_t['T_RM61_min'].plot(ax=ax3, linewidth=2, linestyle='--', color='red', label='T_RM61_min')

    # Plot df_t['T_min'] and df_t['T_max']
    df_t['T_min'].plot(ax=ax3, linestyle='--', color='green', label='T_min_range')
    df_t['T_max'].plot(ax=ax3, linestyle='--', color='green', label='T_max_range')

    # Fill the area below the minimum values
    fill_below = ax3.fill_between(df_t.index, df_t['T_RM61_min'], y2=df_t['T_RM61_min'].min()-0.5, color='red', alpha=0.05, edgecolor='black', linestyle='--')
    fill_below.set_label('Outside T range')

    # Fill the area above the maximum values
    fill_above = ax3.fill_between(df_t.index, df_t['T_RM61_max'], y2=df_t['T_RM61_max'].max()+0.5, color='red', alpha=0.05, edgecolor='black', linestyle='--')

    # Fill in the area between 'T_min' and 'T_max' columns
    fill_between = ax3.fill_between(df_t.index, df_t['T_min'], df_t['T_max'], color='green', alpha=0.2, edgecolor='black', linestyle='--')
    fill_between.set_label('Allowed T ramping range')

    # Customizations for the second subplot
    ax3.set_title('Temperature Data', fontsize=15)
    ax3.set_xlabel('Labels', fontsize=12)
    ax3.set_ylabel('Temperature (°C)', fontsize=12)

    # Customize the x-ticks for the shared x-axis
    ax3.set_xticks(np.arange(0, len(df_dispatch.index)))
    ax3.set_xticklabels(df_dispatch.index)

    # Grid for better visualization
    ax3.grid(True, linestyle='--', alpha=0.5)

    # Combine legends for the second subplot
    lines3, labels3 = ax3.get_legend_handles_labels()
    legend = ax3.legend(lines3, labels3, loc='upper left', fontsize=12)

    # Retrieve the background and edge color from the legend
    legend_facecolor = legend.get_frame().get_facecolor()
    legend_edgecolor = legend.get_frame().get_edgecolor()

    # Calculate the mean of T_RM61 and add text to the top right corner of the second subplot
    mean_t_rm61 = df_t['T_RM61'].mean()
    ax3.text(0.95, 0.95, f'Mean T_RM61: {mean_t_rm61:.2f}', transform=ax3.transAxes,
             fontsize=12, verticalalignment='top', horizontalalignment='right',
             bbox=dict(facecolor=legend_facecolor, edgecolor=legend_edgecolor, boxstyle='round,pad=0.3'))


    #
    df_t['T_dam'].plot(ax=ax4, linewidth=2, color='blue', label='T_dam')
    df_t['T_RM61'].plot(ax=ax4, linewidth=2, color='black', label='T_RM61')
    # Fill in the area between 'T_min' and 'T_max' columns
    fill_between = ax4.fill_between(df_t.index, df_t['T_dam'], df_t['T_RM61'], color='blue', alpha=0.2, edgecolor='black')
    fill_between.set_label('delta_T dam-RM61')
    # Customizations for the second subplot
    ax4.set_title('Temperature Delta Between Dam and RM61', fontsize=15)
    ax4.set_xlabel('Labels', fontsize=12)
    ax4.set_ylabel('Temperature (°C)', fontsize=12)

    # Customize the x-ticks for the shared x-axis
    ax4.set_xticks(np.arange(0, len(df_dispatch.index)))
    ax4.set_xticklabels(df_dispatch.index)

    # Grid for better visualization
    ax4.grid(True, linestyle='--', alpha=0.5)

    # Combine legends for the second subplot
    lines4, labels4 = ax4.get_legend_handles_labels()
    ax4.legend(lines4, labels4, loc='upper left', fontsize=12)
    # Show plot
    plt.tight_layout()
    if save_fig is True:
        plt.savefig(fig_name + '.png', dpi=300)
        logger.info('Saved figure ' + fig_name + '.png')
    plt.show()


def plot_load_serving(df_dispatch, unit_name='',node_name=''):
    fig, ax1 = plt.subplots(nrows=1, ncols=1, figsize=(12, 6), sharex=True)

    # Plot the stacked area chart on the primary y-axis of the first subplot
    df_dispatch[node_name].plot(ax=ax1, alpha=0.6, color='black')
    df_dispatch[unit_name].plot.area(ax=ax1, alpha=0.6)

    # Align the two columns before comparison
    node1, gcd = df_dispatch[node_name].align(df_dispatch[unit_name], join='inner')
    ax1.fill_between(df_dispatch.index, node1, gcd,
                     where=(node1 > gcd),
                     interpolate=True, color='red', hatch='//', edgecolor='black', alpha=0.5)

    # Customizations for the primary y-axis
    ax1.set_title(f'Load serving for {node_name}', fontsize=15)
    ax1.set_ylabel('Energy (MWh)', fontsize=12)

    # Customize the x-ticks for every 24th value
    xticks = np.arange(0, len(df_dispatch.index), 6)
    ax1.set_xticks(xticks)
    ax1.set_xticklabels(df_dispatch.index[xticks])

    # Grid for better visualization
    ax1.grid(True, linestyle='--', alpha=0.5)

    return fig
