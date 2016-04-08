# -*- coding: utf-8 -*-
import bokeh.plotting as plotting
from . import utils


def render_path(common, output_html_filepath, title='Path'):
    '''
    Create a HTML-based visualization of the gaze path.
    '''
    lxs = common.get_stream_values('gazelib/gaze/left_eye_x_relative')
    lys = common.get_stream_values('gazelib/gaze/left_eye_y_relative')
    rxs = common.get_stream_values('gazelib/gaze/right_eye_x_relative')
    rys = common.get_stream_values('gazelib/gaze/right_eye_y_relative')

    p = plotting.figure(title=title, x_axis_label='X', y_axis_label='Y',
                        plot_width=640, plot_height=480,
                        x_range=(-0.2, 1.2), y_range=(-0.2, 1.2))

    # Render screen rectangle
    p.quad(left=[0.0], right=[1.0], top=[0.0], bottom=[1.0],
           line_width=1, line_color='black', fill_alpha=0)

    # Visualize only valid points.
    # We do that by visualizing valid subpaths

    def validator(x):
        return x[0] is not None and x[1] is not None

    lpaths = utils.get_valid_sublists(zip(lxs, lys), validator)
    rpaths = utils.get_valid_sublists(zip(rxs, rys), validator)

    for valid_path in lpaths:
        valid_xs = list(map(lambda x: x[0], valid_path))
        valid_ys = list(map(lambda x: x[1], valid_path))

        p.cross(valid_xs, valid_ys, size=10, line_color='blue')
        p.line(valid_xs, valid_ys, line_width=1, line_color='blue')

    for valid_path in rpaths:
        valid_xs = list(map(lambda x: x[0], valid_path))
        valid_ys = list(map(lambda x: x[1], valid_path))

        p.cross(valid_xs, valid_ys, size=10, line_color='red')
        p.line(valid_xs, valid_ys, line_width=1, line_color='red')
        # Red as Right

    # Display start points.
    lfirst = lpaths[0][0]
    rfirst = rpaths[0][0]
    # Width and height in x_axis and y_axis units.
    p.oval(x=lfirst[0], y=lfirst[1], width=0.17, height=0.2,
           line_color='blue', fill_alpha=0)
    p.oval(x=rfirst[0], y=rfirst[1], width=0.17, height=0.2,
           line_color='red', fill_alpha=0)

    plotting.output_file(output_html_filepath, title)
    plotting.save(p)


def render_path_for_each_event(common, event_tag, output_html_filepath):
    pass


def render_overview(common, output_html_filepath, title='Overview'):
    '''
    Create HTML-based visualization from all streams and events.
    Does not understand stream or event semantics like gaze paths for example.
    '''

    # Collect figures together
    figs = []

    def to_ms(micros):
        return int(round(micros / 1000))

    #########
    # Streams
    #########

    stream_names = sorted(common.list_stream_names())
    for stream_name in stream_names:
        tl_name = common.get_stream_timeline_name(stream_name)
        x = list(map(to_ms, common.get_timeline(tl_name)))
        y = common.get_stream_values(stream_name)

        # Get valid substreams
        sl = utils.get_valid_sublists_2d(x, y)

        fig = plotting.figure(title=stream_name, x_axis_label='time (ms)',
                              plot_width=1000, plot_height=300,
                              toolbar_location=None)

        for xs, ys in sl:
            fig.line(xs, ys, line_color='black')

        # Emphasize gaps with red line.
        # Loop pairwise, fill gaps.
        # TODO Optimize. Currently very slow.
        for i in range(len(sl) - 1):
            xs0, ys0 = sl[i]
            xs1, ys1 = sl[i + 1]
            # Extrapolate from last known value
            x0 = xs0[-1]
            x1 = xs1[0]
            y = ys0[-1]
            fig.line(x=[x0, x1], y=[y, y], line_width=1, line_color='red')

        figs.append(fig)

    ########
    # Events
    ########

    # Create a row for each event. X is time.
    evs = common.list_events()

    # Visualize in start time, then duration order.
    # Recent topmost, hence minus. If start time same, longest topmost.
    def order_key(ev):
        t0 = -ev['range'][0]
        dur = ev['range'][1] + t0
        return (t0, dur)

    evs = sorted(evs, key=order_key)

    fig = plotting.figure(title='Events', y_range=(-1, len(evs)),
                          plot_width=1000,
                          x_axis_label='time (ms)',
                          toolbar_location=None)

    # Hide event indices and draw custom text instead.
    fig.yaxis.visible = None

    for i, ev in enumerate(evs):
        t0 = to_ms(ev['range'][0])
        t1 = to_ms(ev['range'][1])
        fig.text(text=[', '.join(ev['tags'])], y=[i + 0.1], x=[t0])

        fig.line(x=[t0, t1], y=[i, i], line_width=6, line_color='black')
        # Mark where events start and end.
        fig.line(x=[t0, t0], y=[i - 0.1, i + 0.1],
                 line_width=2, line_color='black')
        fig.line(x=[t1, t1], y=[i - 0.1, i + 0.1],
                 line_width=2, line_color='black')

    figs.append(fig)

    # Lay out multiple figures
    p = plotting.vplot(*figs)
    # Save
    plotting.output_file(output_html_filepath, title)
    plotting.save(p)
