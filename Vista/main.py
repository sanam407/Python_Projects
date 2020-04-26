""" From Vista to Python - Visualization of reachable sets
This example code reads JSON files exported from Vista and perform visualizations
"""

# Data Handling
import json
import numpy as np
import math
import base64

# Bokeh libraries
from bokeh.layouts import column
from bokeh.io import curdoc
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, FileInput, Div, HoverTool


# JSON files contain color in the form of rgb, html rendering requires conversion to hex format
def rgb_to_hex(rgb):
    return '%02x%02x%02x' % rgb


# Details in text in left column
def add_details(new_text):
    left_panel.children.insert(len(left_panel.children), Div(text=new_text))


# Refresh plot whenever new file is selected
def clear_old_data():
    for all_data in source:
        all_data.data = {k: [] for k in all_data.data}
    if len(left_panel.children) > 0:
        left_panel.children = []


def show_plot(attr, old, new):
    clear_old_data()  # Refresh plot whenever new file is selected
    global source  # always keep one source & append all values so that it can be removed when loading new files
    json_file = base64.b64decode(new).decode('utf-8')  # Read data from JSON file
    data = json.loads(json_file)

    # -----  Draw Paths with Waypoints and joining line  ----- #
    for paths in data['paths']:
        coord_x = []
        coord_y = []
        rgb = paths['pathColor']
        path_color = (rgb['r'] * 255, rgb['g'] * 255, rgb['b'] * 255)

        for wps in paths['pathwaypoints']:
            coord_x.append(wps['x'])
            coord_y.append(wps['z'])

        source.append(ColumnDataSource(data=dict(
            x=coord_x,
            y=coord_y,
            desc=np.full((len(coord_x)), str(paths['P_name'])),
        )))
        # Plot for path line - as lines
        plot.line('x', 'y', color=path_color, source=source[len(source) - 1],
                  legend_label="Path: " + str(paths['P_name']))
        # Plot for waypoints - as circles
        plot.circle('x', 'y', fill_color=path_color, line_color=path_color, size=8, source=source[len(source) - 1],
                    legend_label="Waypoints of " + str(paths['P_name']))

    target_text = ""  # text for details window

    # -----  Draw Reachable Regions  ----- #
    for action in data['actions']:
        x_reachable = []  # X values of reachable sets
        y_reachable = []  # Y values of reachable sets
        width = []  # width of reachable regions
        height = []  # height of reachable regions
        time_reachable = []  # Time when a sets becomes reachable
        angle_radians = []  # Angle of reachable set

        path_index = action['pathIndex']
        rgb = data['paths'][path_index]['pathColor']
        path_color = (rgb['r'] * 255, rgb['g'] * 255, rgb['b'] * 255)

        for reachableXs in action['reachableSetsX']:
            x_low = round(reachableXs['lo'], 2)
            x_high = round(reachableXs['hi'], 2)
            x_reachable.append((x_low + x_high) / 2)
            time_reachable.append(str(data['paths'][path_index]['P_name']) + " | Reachable Set interval at time: "
                                  + str(round(reachableXs['time'] / 60, 2)) + "sec")
            width.append(abs(x_high - x_low))
            angle_radians = reachableXs['angle']

        for reachableYs in action['reachableSetsZ']:
            y_low = round(reachableYs['lo'], 2)
            y_high = round(reachableYs['hi'], 2)
            y_reachable.append((y_low + y_high) / 2)
            height.append(abs(y_high - y_low))

        source.append(ColumnDataSource(data=dict(
            x=x_reachable,
            y=y_reachable,
            w=width,
            h=height,
            desc=time_reachable
        )))
        # text to show in details window
        target_text += "<br>" + "<b>Trajectory: </b>" + str(action['myName']) + "<br>" + \
                       '<i>Path name: </i>' + str(data['paths'][path_index]['P_name']) + '<br>' + \
                       '<i>start time: </i>' + str(action['starttime'] / 60) + 'sec, speed: ' + \
                       str(action['mySpeed']) + 'km/h <br>' + \
                       '<i>starting position range: </i>X[' + str(round(x_reachable[0], 2)) + ".." + \
                       str(round(x_reachable[0] + width[0], 2)) + "]" + \
                       ",Y[" + str(round(y_reachable[0], 2)) + ".." + str(
            round(y_reachable[0] + height[0], 2)) + "]<br>"
        index = len(x_reachable) - 1
        # text to show in details window
        target_text += '<i>ending position range: </i>X[' + str(round(x_reachable[index], 2)) + ".." + \
                       str(round(x_reachable[index] + width[index], 2)) + "]" + \
                       ",Y[" + str(round(y_reachable[index], 2)) + ".." + \
                       str(round(y_reachable[index] + height[index], 2)) + "] <br>"

        # Plotting all reachable regions - as rectangles (Box representation for sets)
        plot.rect('x', 'y', 'w', 'h', angle=angle_radians, color=path_color, alpha=0.3, source=source[len(source) - 1],
                  legend_label="Reachable Intervals for trajectory " + str(action['myName']))
    add_details(target_text)

    # -----  Draw Unsafe Regions  ----- #
    target_text = '<b>Possible collisions in range:</b><br>'
    for action in data['actions']:
        x_unsafe = []
        y_unsafe = []
        unsafe_width = []
        unsafe_height = []
        radians_unsafe = []
        time_reachable = []
        timer = []
        if len(action['unsafeSetsX']) > 0:
            for reachableXs in action['unsafeSetsX']:
                if len(reachableXs) > 0:
                    x_low = reachableXs['lo']
                    x_hi = reachableXs['hi']
                    x_unsafe.append(x_low)
                    time_reachable.append(str(data['paths'][path_index]['P_name']) + " | Reachable Set at time: " + str(
                        round(reachableXs['time'] / 60, 2)) + "sec")
                    timer.append(round(reachableXs['time'] / 60, 2))
                    radians_unsafe.append(math.atan2(x_hi, x_low))
                    unsafe_width.append(abs(x_hi - x_low))
        if len(action['unsafeSetsZ']) > 0:
            for reachableYs in action['unsafeSetsZ']:
                if len(reachableYs) > 0:
                    y_low = reachableYs['lo']
                    y_hi = reachableYs['hi']
                    y_unsafe.append(y_low)
                    unsafe_height.append(abs(y_hi - y_low))

        source.append(ColumnDataSource(data=dict(
            x=x_unsafe,
            y=y_unsafe,
            w=unsafe_width,
            h=unsafe_height,
            desc=time_reachable
        )))
        # Plotting all unsafe regions - as rectangles (Box representation for sets)
        plot.rect('x', 'y', 'w', 'h', angle=angle_radians, color='yellow', alpha=0.5,
                  source=source[len(source) - 1], legend_label="Unsafe Region")
        index = 0
        for xx in x_unsafe:
            target_text += 'X[' + str(round(xx, 2)) + ".." + str(round(xx + unsafe_width[index], 2)) + "]" + \
                           ",Y[" + str(round(y_unsafe[index], 2)) + ".." + str(
                round(y_unsafe[index] + unsafe_height[index], 2)) + \
                           "], at time " + str(timer[index]) + "sec <br>"
            index += 1
        if index == 0:
            target_text = ''  # no collision found

    # add all the details in detail window
    add_details(target_text)

    # Interactive tools for plot
    plot.add_tools(
        HoverTool(
            toggleable=False,
            tooltips=[
                ("(x,y)", "($x, $y)"),
                ("Path", "@desc"),
            ],
        )
    )
    plot.legend.location = "top_left"  # (0,-30)
    plot.legend.click_policy = "hide"


# Global variables
source = []  # x-y coordinate data
TOOLTIPS = [
    ("(x,y)", "($x, $y)"),
    ("Path", "@desc"),
]

# Set up the figure(s) for plot
plot = figure(name="plot2", plot_width=1200, plot_height=700, x_range=(-62, 62), y_range=(-35, 35),
              # sizing_mode="stretch_both",
              title="Vista Reachability Analysis", tooltips=TOOLTIPS, toolbar_location="below",
              tools="pan,wheel_zoom")

# plot-figure visual settings
img_path = "https://raw.githubusercontent.com/sanam407/Simulator/master/AstaZero.png"
plot.image_url(url=[img_path], x=-62, y=35, w=124, h=70)
plot.x_range.bounds = (-62, 62)
plot.y_range.bounds = (-35, 35)
plot.background_fill_color = "#252e38"
plot.border_fill_color = "#252e38"
plot.grid.grid_line_color = None
plot.axis.axis_label = None
plot.axis.visible = False
plot.outline_line_color = '#41454a'
plot.title.align = "center"
plot.title.text_color = "white"
plot.title.text_font_size = "15px"

# Adding plot-figure to root of current html document
curdoc().add_root(plot)

# Importing JSON files
file_input = FileInput(accept=".json", name="top")  # "Choose JSOn file exported from Vista"
file_input.on_change("value", show_plot)
curdoc().add_root(file_input)

# Column layout setting
left_panel = column(Div(text="No File Selected"), width=400, name="left")
curdoc().add_root(left_panel)

# Title of current document
curdoc().title = 'Vista Reachability Analysis'
