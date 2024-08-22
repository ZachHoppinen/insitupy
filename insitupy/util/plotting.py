"""
Functionality for plotting SnowProfile and SnowCampaign objects.
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from insitupy.util.strings import StringManager

import numpy as np
import pandas as pd
import xarray as xr
import matplotlib.pyplot as plt

from insitupy.util.strings import StringManager

import re

"""
Creates a new colormap from a slice or two of an old one and sets a new mid point for the new colormap.
"""
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import AxesGrid
import matplotlib.patches as patches
from mpl_toolkits.axes_grid1 import make_axes_locatable
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.legend_handler import HandlerLineCollection
from matplotlib.collections import LineCollection

class HandlerColorLineCollection(HandlerLineCollection):
    """
    Multicolor line collection to make fake legends with.
    """
    def create_artists(self, legend, artist ,xdescent, ydescent,
                        width, height, fontsize,trans):
        x = np.linspace(0,width,self.get_numpoints(legend)+1)
        y = np.zeros(self.get_numpoints(legend)+1)+height/2.-ydescent
        points = np.array([x, y]).T.reshape(-1, 1, 2)
        segments = np.concatenate([points[:-1], points[1:]], axis=1)
        lc = LineCollection(segments, cmap=artist.cmap,
                     transform=trans)
        lc.set_array(x)
        lc.set_linewidth(artist.get_linewidth())
        return [lc]

def shiftedColorMap(cmap, start=0, midpoint=0.5, stop=1.0, name='shiftedcmap'):
    '''
    Function to offset the "center" of a colormap. Useful for
    data with a negative min and positive max and you want the
    middle of the colormap's dynamic range to be at zero.

    Input
    -----
      cmap : The matplotlib colormap to be altered
      start : Offset from lowest point in the colormap's range.
          Defaults to 0.0 (no lower offset). Should be between
          0.0 and `midpoint`.
      midpoint : The new center of the colormap. Defaults to 
          0.5 (no shift). Should be between 0.0 and 1.0. In
          general, this should be  1 - vmax / (vmax + abs(vmin))
          For example if your data range from -15.0 to +5.0 and
          you want the center of the colormap at 0.0, `midpoint`
          should be set to  1 - 5/(5 + 15)) or 0.75
      stop : Offset from highest point in the colormap's range.
          Defaults to 1.0 (no upper offset). Should be between
          `midpoint` and 1.0.
    '''
    cdict = {
        'red': [],
        'green': [],
        'blue': [],
        'alpha': []
    }

    # regular index to compute the colors
    reg_index = np.linspace(start, stop, 257)

    # shifted index to match the data
    shift_index = np.hstack([
        np.linspace(0.0, midpoint, 128, endpoint=False), 
        np.linspace(midpoint, 1.0, 129, endpoint=True)
    ])

    for ri, si in zip(reg_index, shift_index):
        r, g, b, a = cmap(ri)

        cdict['red'].append((si, r, r))
        cdict['green'].append((si, g, g))
        cdict['blue'].append((si, b, b))
        cdict['alpha'].append((si, a, a))

    newcmap = matplotlib.colors.LinearSegmentedColormap(name, cdict)
    # plt.register_cmap(cmap=newcmap)

    return newcmap

def plot_profile(profile: xr.Dataset):
    fig, axes = plt.subplots(2, 3, width_ratios=[6, 1, 4], figsize = (12, 8))

        # D=Dry, M=Moist, W=Wet, V=Very Wet, S=Soaked
    cmap = plt.get_cmap('Blues')
    # wetness_dict = {'D': 'lightblue', 'M': "salmon", "W": "tomato", "V": "red", "S": "darkred"}
    wetness_dict = {'D': cmap(0.3), 'M': cmap(0.5), "W": cmap(0.7), "V": cmap(0.9), "S": cmap(1.0)}

    layertext = []

    hardness_ns = {'F': 0, '4F': 1, '1F': 2, 'P': 3, 'K': 4, 'I': 5}
    density_cmap = plt.get_cmap('plasma')
    # Remove the middle 40% of the RdBu_r colormap
    interval = np.hstack([np.linspace(0, 0.3), np.linspace(0.5, 1)])
    colors = plt.cm.RdBu(interval)
    cmap = LinearSegmentedColormap.from_list('name', colors)
    temp_cmap = shiftedColorMap(cmap, 0, 0.1, 1, 'shifted_cut_cmap1')

    # interval = np.hstack([np.linspace(1, 0.5), np.linspace(0.3, 0)])
    # colors = plt.cm.RdBu(interval)
    # cmap = LinearSegmentedColormap.from_list('name', colors)
    # temp_cmap = shiftedColorMap(cmap, 0, 0.1, 1, 'shifted_cut_cmap1')
    # lwc_cmap = shiftedColorMap(cmap, 0, 0.1, 1)
    
    colors = plt.cm.Blues(np.linspace(0.2, 1))
    cmap = LinearSegmentedColormap.from_list('name', colors)
    lwc_cmap = cmap
    permittiv_cmap = plt.get_cmap('plasma')


    iteration_number = {'_a': 0.3, '_b': 0.1, '_c': 0.5, 'avg_': 1.0}
    iter_list = ['_a', '_b', '_c', 'avg_']

    ax_density, ax_middle, ax_temp = axes[0]
    
    # squish 0,0 and 0,1 together
    gs = axes[0, 1].get_gridspec()
    for ax in axes[0, :2]: ax.remove()
    ax_density = fig.add_subplot(gs[0, :2])

    ax_strat, ax_layernotes, ax_dielectric = axes[1]
    # plotted = False

    for var in profile.data_vars:
        if profile[var].count() == 0: continue

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
            da = da.dropna('z')

            # sort bottom appropriately
            bottom = profile[var].attrs['samples'].values
            if is_ascending(da.z.data):
                if not is_ascending(np.array(bottom)):
                    bottom = reversed(bottom)

            for i, b in zip(da, bottom):
                if np.isnan(i.data): continue
                
                height = i.z - b
                mid = i.z - height/ 2

                if 'manual_wetness' in profile.data_vars:
                    wetness = profile['manual_wetness'].sel(z = i.z).data.ravel()[0]
                    if wetness not in wetness_dict.keys():
                        color = 'grey'
                    else:
                        color = wetness_dict[wetness]
                else:
                    color = 'lightblue'
                
                ax_strat.barh(mid, i.data + 1, height, color = color, edgecolor = 'darkblue')

                if 'grain_type' in profile.data_vars:
                    grain_type = profile['grain_type'].sel(z = i.z).data.ravel()[0]
                    if isinstance(grain_type, float) and np.isnan(grain_type): grain_type = ''
                grain_size = ''
                if 'grain_size' in profile.data_vars:
                    grain_size = profile['grain_size'].sel(z = i.z).data.ravel()[0]
                    if isinstance(grain_size, float) and np.isnan(grain_size): grain_size = ''

                if isinstance(grain_size, float) and np.isnan(grain_size): grain_size = '- mm'
                str_layer = f'{grain_type} @ {grain_size}'
                # add new line every 15 charactesr

                if height > 3:
                    xy = float(-0.2), float(mid.data.ravel()[0])
                    ax = ax_layernotes
                    str_layer = re.sub("(.{25})", "\\1\n", str_layer, 0, re.DOTALL)
                else:
                    xy = float(6.5), float(mid.data.ravel()[0])
                    ax = ax_strat
                    str_layer = re.sub("(.{20})", "\\1\n", str_layer, 0, re.DOTALL)
                ax.text(*xy, str_layer, ha = 'left', va= 'center')
            continue
        elif 'manual_wetness' in var:
            continue            
            
        else: continue

        if iteration: color = cmap(iteration)
        else: color = cmap(1.0)
        
        if 'temp' in var or 'lwc' in var: color = 'black'

        ax.scatter(profile[var], profile.z, marker = 'x', zorder = 1e2, s = 2, color = color)

        if 'avg' in var:
            linewidth = 5
            color = 'k'
            zorder = 1e4
            linestyle = '--'
        else:
            linewidth = 2
            zorder = 1
            linestyle = '-'
        
        if 'temp' not in var and 'lwc' not in var:
            ax.plot(profile[var].dropna('z'), profile[var].dropna('z').z, linestyle = linestyle, zorder = zorder, label = label, color = color, linewidth= linewidth)
        else:
            tinter = profile[var].dropna('z').interp(z = np.linspace(0, np.nanmax(profile.z.data), 200))
            if np.abs(tinter).max().data == 0:
                temp_c = np.abs(tinter.data - 0.0001)
            else:
                temp_c = np.abs(tinter.data / np.abs(tinter).max().data)
            ax.scatter(tinter.data, tinter.z, color = cmap(temp_c))

        ax.legend()

    # make fake multicolored lines for temp and lwc
    for ax, cmap, label in zip([ax_temp, ax_dielectric], [temp_cmap, lwc_cmap], ['Temp [°C]', 'LWC [%]']):
        handles, labels = ax.get_legend_handles_labels()

        lc = LineCollection([], cmap=cmap,
                            norm=plt.Normalize(0, 10), linewidth=3)

        handles.append(lc)
        labels.append(label)
        ax.legend(handles = handles, labels = labels,\
            handler_map={lc: HandlerColorLineCollection(numpoints=10)}, framealpha=1)

    dt = pd.to_datetime(profile.time.data[0]).strftime('%Y-%m-%d %T')
    x, y = profile.x.data[0], profile.y.data[0]
    plt.suptitle(f'Snow Pit ID: {profile.id.data[0]}\n Time: {dt}\nLocation: x= {x} y = {y}')

    for ax, label in zip([ax_density,ax_temp,ax_strat, ax_dielectric ], ['Density [kg/m3]', 'Temperature [°C]', 'Hand Hardness', 'Dielectric Permittivity/LWC []']):
        ymax = max(profile.z) + max(profile.z) * 0.08
        ax.set_ylim(0, ymax)

        # ax.set_xlabel(label)


    for ax in [ax_density, ax_strat]:
        ax.set_ylabel(f"{profile.z.attrs['long_name']} [{profile.z.attrs['units']}]")

    ax_density.invert_xaxis()
    ax_temp.invert_xaxis()

    for ax in axes[:, 2]:
        ax.set_yticklabels([])

    ax_strat.set_xticks([1, 2, 3, 4, 5, 6])
    ax_strat.set_xticklabels(hardness_ns)
    ax_strat.invert_xaxis()
    ax_strat.set_xlim(right = -0.1, left = 6.6)

    ax_layernotes.axis('off')

    if ax_temp.get_xlim()[1] < 0: ax_temp.set_xlim(left = 0.2)

    ax_layernotes.set_ylim(ax_strat.get_ylim())
    for ax, title in zip([ax_density, ax_temp, ax_strat, ax_layernotes, ax_dielectric],\
        ["Density [kg/m3]", "Temperature [°]", "Stratigraphy", "", "Permittivity/ LWC"]):
        ax.set_title(title)

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

def is_ascending(arr):
    return np.all(arr[:-1] <= arr[1:])