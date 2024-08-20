"""
Functionality for plotting SnowProfile and SnowCampaign objects.
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from insitupy.util.strings import StringManager

def plot_profile(profile):
    hardness_ns = {'F': 0, '4F': 1, '1F': 2, 'P': 3, 'K': 4, 'I': 5}
    density_cmap = plt.get_cmap('cividis')
    temp_cmap = plt.get_cmap('magma')
    lwc_cmap = plt.get_cmap('hsv')
    permittiv_cmap = plt.get_cmap('twilight')


    iteration_number = {'_a': 0.2, '_b': 0.5, '_c': 0.8, 'avg_': 0.0}
    iter_list = ['_a', '_b', '_c', 'avg_']

    fig, axes = plt.subplots(2, 2, width_ratios=[3, 1], figsize = (8, 6))
    ax_density, ax_temp = axes[0]
    ax_strat, ax_dielectric = axes[1]
    plotted = False

    for var in profile.data_vars:
        print(var)
        label = ' '.join(var.split('_')).capitalize()
        if any([l in var for l in iter_list]):
            iter_n = iter_list[np.where([l in var for l in iter_list])[0][0]]
            iteration = iteration_number[iter_n]
        else:
            iteration = None
        
        # if plotted and plotted not in var: ax = ax.twiny()

        if 'density' in var:
            cmap = density_cmap
            ax = ax_density
        elif 'temp' in var:
            cmap = temp_cmap
            ax = ax_temp
        elif 'lwc' in var:
            cmap = lwc_cmap
            ax = ax_dielectric
        elif 'permittivity' in var:
            cmap = permittiv_cmap
            ax = ax_dielectric
        elif 'hand_hardness' in var:
            da = _convert_handhardness_to_numeric(profile)
            for i in da:
                if np.isnan(i.data): continue
                height = i.z - i.bottom
                mid = i.z - height/ 2
                ax_strat.barh(mid, i.data, height, color = 'C0', edgecolor = 'purple')
                if 'grain_type' in profile.data_vars:
                    grain_type = profile['grain_type'].sel(z = i.z).data.ravel()[0]
                    if isinstance(grain_type, float) and np.isnan(grain_type): grain_type = ''
                grain_size = ''
                if 'grain_size' in profile.data_vars:
                    grain_size = profile['grain_size'].sel(z = i.z).data.ravel()[0]
                    if isinstance(grain_size, float) and np.isnan(grain_size): grain_size = ''
                    
                xy = float((i.data + i.data * 0.1).ravel()[0]), float(mid.data.ravel()[0])
                ax_strat.annotate(f'{grain_type} @ {grain_size}', xy, xycoords='data', ha = 'right', va= 'center')
            continue
        elif 'manual_wetness' in var:
            continue            
            
        else: continue

            
        if iteration: color = cmap(iteration)
        else: color = cmap(0.5)

        ax.scatter(profile[var], profile.z, marker = 'x', color = color)
        ax.plot(profile[var].dropna('z'), profile[var].dropna('z').z, label = label, color = color)
        
        if iteration:
            ax.legend()
        
        plotted = var.strip(iter_n)

    dt = pd.to_datetime(profile.time.data[0]).strftime('%Y-%m-%dT%T')
    x, y = profile.x.data[0], profile.y.data[0]
    plt.suptitle(f'ID: {profile.id.data[0]} @ {dt}\nx= {x} y = {y}')

    for ax, label in zip(axes.ravel(), ['Density [kg/m3]', 'Temperature [°C]', '', 'Dielectric Permittivity/LWC []']):
        ymax = max(profile.z) + max(profile.z) * 0.08
        ax.set_ylim(0, ymax)

        ax.set_xlabel(label)


    for ax in axes[:, 0]:
        ax.set_ylabel(f"{profile.z.attrs['long_name']} [{profile.z.attrs['units']}]")

    ax_density.invert_xaxis()
    ax_temp.invert_xaxis()

    for ax in axes[:, 1]:
        ax.set_yticklabels([])

    ax_strat.set_xticks([0, 1, 2, 3, 4, 5])
    ax_strat.set_xticklabels(hardness_ns)
    ax_strat.invert_xaxis()
    ax_strat.set_xlim(right = -0.1, left = 5.1)

    if ax_temp.get_xlim()[1] < 0: ax_temp.set_xlim(left = 0.2)
    ax_temp.axvline(0, color = 'red', linestyle = '--')
    plt.tight_layout()

    return fig

def _convert_handhardness_to_numeric(ds):
    da = ds['hand_hardness'].copy()
    hardness_ns = {'F': 0, '4F': 1, '1F': 2, 'P': 3, 'K': 4, 'I': 5}
    hss = []

    for h in ds['hand_hardness'].data:
        if isinstance(h, str):hss.append(hardness_ns[h])
        elif np.isnan(h): hss.append(np.nan)
        else: raise ValueError
    da.data = hss

    return da