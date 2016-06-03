""" Plotly Offline
    A module to use Plotly's graphing library with Python
    without connecting to a public or private plotly enterprise
    server.
"""
from __future__ import absolute_import

import json
import os
import uuid
import warnings
from pkg_resources import resource_string
import webbrowser

import plotly
from plotly import tools, utils
from plotly.exceptions import PlotlyError

try:
    import IPython
    from IPython.display import HTML, display
    _ipython_imported = True
except ImportError:
    _ipython_imported = False

try:
    import matplotlib
    _matplotlib_imported = True
except ImportError:
    _matplotlib_imported = False

__PLOTLY_OFFLINE_INITIALIZED = False


def download_plotlyjs(download_url):
    warnings.warn('''
        `download_plotlyjs` is deprecated and will be removed in the
        next release. plotly.js is shipped with this module, it is no
        longer necessary to download this bundle separately.
    ''', DeprecationWarning)
    pass


def get_plotlyjs():
    path = os.path.join('offline', 'plotly.min.js')
    plotlyjs = resource_string('plotly', path).decode('utf-8')
    return plotlyjs


def init_notebook_mode(connected=False):
    """
    Initialize plotly.js in the browser if it hasn't been loaded into the DOM
    yet. This is an idempotent method and can and should be called from any
    offline methods that require plotly.js to be loaded into the notebook dom.

    Keyword arguments:

    connected (default=False) -- If True, the plotly.js library will be loaded
    from an online CDN. If False, the plotly.js library will be loaded locally
    from the plotly python package

    Use `connected=True` if you want your notebooks to have smaller file sizes.
    In the case where `connected=False`, the entirety of the plotly.js library
    will be loaded into the notebook, which will result in a file-size increase
    of a couple megabytes. Additionally, because the library will be downloaded
    from the web, you and your viewers must be connected to the internet to be
    able to view charts within this notebook.

    Use `connected=False` if you want you and your collaborators to be able to
    create and view these charts regardless of the availability of an internet
    connection. This is the default option since it is the most predictable.
    Note that under this setting the library will be included inline inside
    your notebook, resulting in much larger notebook sizes compared to the case
    where `connected=True`.
    """
    if not _ipython_imported:
        raise ImportError('`iplot` can only run inside an IPython Notebook.')

    global __PLOTLY_OFFLINE_INITIALIZED

    if connected:
        # Inject plotly.js into the output cell
        script_inject = (
            ''
            '<script>'
            'requirejs.config({'
            'paths: { '
            # Note we omit the extension .js because require will include it.
            '\'plotly\': [\'https://cdn.plot.ly/plotly-latest.min\']},'
            '});'
            'if(!window.Plotly) {{'
            'require([\'plotly\'],'
            'function(plotly) {window.Plotly=plotly;});'
            '}}'
            '</script>'
        )
    else:
        # Inject plotly.js into the output cell
        script_inject = (
            ''
            '<script type=\'text/javascript\'>'
            'if(!window.Plotly){{'
            'define(\'plotly\', function(require, exports, module) {{'
            '{script}'
            '}});'
            'require([\'plotly\'], function(Plotly) {{'
            'window.Plotly = Plotly;'
            '}});'
            '}}'
            '</script>'
            '').format(script=get_plotlyjs())

    display(HTML(script_inject))
    __PLOTLY_OFFLINE_INITIALIZED = True


def _plot_html(figure_or_data, show_link, link_text, validate,
               default_width, default_height, global_requirejs,
               download=False):

    figure = tools.return_figure_from_figure_or_data(figure_or_data, validate)

    width = figure.get('layout', {}).get('width', default_width)
    height = figure.get('layout', {}).get('height', default_height)

    try:
        float(width)
    except (ValueError, TypeError):
        pass
    else:
        width = str(width) + 'px'

    try:
        float(width)
    except (ValueError, TypeError):
        pass
    else:
        width = str(width) + 'px'

    plotdivid = uuid.uuid4()
    jdata = json.dumps(figure.get('data', []), cls=utils.PlotlyJSONEncoder)
    jlayout = json.dumps(figure.get('layout', {}), cls=utils.PlotlyJSONEncoder)

    config = {}
    config['showLink'] = show_link
    config['linkText'] = link_text
    jconfig = json.dumps(config)

    # TODO: The get_config 'source of truth' should
    # really be somewhere other than plotly.plotly
    plotly_platform_url = plotly.plotly.get_config().get('plotly_domain',
                                                         'https://plot.ly')
    if (plotly_platform_url != 'https://plot.ly' and
            link_text == 'Export to plot.ly'):

        link_domain = plotly_platform_url\
            .replace('https://', '')\
            .replace('http://', '')
        link_text = link_text.replace('plot.ly', link_domain)

    script = 'Plotly.newPlot("{id}", {data}, {layout}, {config})'.format(
        id=plotdivid,
        data=jdata,
        layout=jlayout,
        config=jconfig)

    optional_line1 = ('require(["plotly"], function(Plotly) {{ '
                      if global_requirejs else '')
    optional_line2 = ('}});' if global_requirejs else '')

    plotly_html_div = (
        ''
        '<div id="{id}" style="height: {height}; width: {width};" '
        'class="plotly-graph-div">'
        '</div>'
        '<script type="text/javascript">' +
        optional_line1 +
        'window.PLOTLYENV=window.PLOTLYENV || {{}};'
        'window.PLOTLYENV.BASE_URL="' + plotly_platform_url + '";'
        '{script}' +
        optional_line2 +
        '</script>'
        '').format(
        id=plotdivid, script=script,
        height=height, width=width)

    return plotly_html_div, plotdivid, width, height, plotdivid


def iplot(figure_or_data, show_link=True, link_text='Export to plot.ly',
          validate=True, download_image=False, format='png',
          width=800, height=600, filename='newplot'):
    """
    Draw plotly graphs inside an IPython notebook without
    connecting to an external server.
    To save the chart to Plotly Cloud or Plotly Enterprise, use
    `plotly.plotly.iplot`.
    To embed an image of the chart, use `plotly.image.ishow`.

    figure_or_data -- a plotly.graph_objs.Figure or plotly.graph_objs.Data or
                      dict or list that describes a Plotly graph.
                      See https://plot.ly/python/ for examples of
                      graph descriptions.

    Keyword arguments:
    show_link (default=True) -- display a link in the bottom-right corner of
                                of the chart that will export the chart to
                                Plotly Cloud or Plotly Enterprise
    link_text (default='Export to plot.ly') -- the text of export link
    validate (default=True) -- validate that all of the keys in the figure
                               are valid? omit if your version of plotly.js
                               has become outdated with your version of
                               graph_reference.json or if you need to include
                               extra, unnecessary keys in your figure.

    Example:
    ```
    from plotly.offline import init_notebook_mode, iplot
    init_notebook_mode()
    iplot([{'x': [1, 2, 3], 'y': [5, 2, 7]}])
    ```
    """
    if not __PLOTLY_OFFLINE_INITIALIZED:
        raise PlotlyError('\n'.join([
            'Plotly Offline mode has not been initialized in this notebook. '
            'Run: ',
            '',
            'import plotly',
            'plotly.offline.init_notebook_mode() '
            '# run at the start of every ipython notebook',
        ]))
    if not tools._ipython_imported:
        raise ImportError('`iplot` can only run inside an IPython Notebook.')

    plot_html, plotdivid, width, height, plot_id = _plot_html(
        figure_or_data, show_link, link_text, validate,
        '100%', 525, global_requirejs=True, download=download_image)

    display(HTML(plot_html))

    # Use the plot id to download the image now:

    script = ('<script>'
              'Plotly.downloadImage(\'{plot_id}\', {{format: \'{format}\', '
              'height: {height}, width: {width}, filename: \'{filename}\'}});'
              '</script>'
             ).format(format=format, width=width, height=height,
                      filename=filename, plot_id=plot_id)

    display(HTML(script))

def plot(figure_or_data,
         show_link=True, link_text='Export to plot.ly',
         validate=True, output_type='file',
         include_plotlyjs=True,
         filename='temp-plot.html',
         auto_open=True):
    """ Create a plotly graph locally as an HTML document or string.

    Example:
    ```
    from plotly.offline import plot
    import plotly.graph_objs as go

    plot([go.Scatter(x=[1, 2, 3], y=[3, 2, 6])], filename='my-graph.html')
    ```
    More examples below.

    figure_or_data -- a plotly.graph_objs.Figure or plotly.graph_objs.Data or
                      dict or list that describes a Plotly graph.
                      See https://plot.ly/python/ for examples of
                      graph descriptions.

    Keyword arguments:
    show_link (default=True) -- display a link in the bottom-right corner of
        of the chart that will export the chart to Plotly Cloud or
        Plotly Enterprise
    link_text (default='Export to plot.ly') -- the text of export link
    validate (default=True) -- validate that all of the keys in the figure
        are valid? omit if your version of plotly.js has become outdated
        with your version of graph_reference.json or if you need to include
        extra, unnecessary keys in your figure.
    output_type ('file' | 'div' - default 'file') -- if 'file', then
        the graph is saved as a standalone HTML file and `plot`
        returns None.
        If 'div', then `plot` returns a string that just contains the
        HTML <div> that contains the graph and the script to generate the
        graph.
        Use 'file' if you want to save and view a single graph at a time
        in a standalone HTML file.
        Use 'div' if you are embedding these graphs in an HTML file with
        other graphs or HTML markup, like a HTML report or an website.
    include_plotlyjs (default=True) -- If True, include the plotly.js
        source code in the output file or string.
        Set as False if your HTML file already contains a copy of the plotly.js
        library.
    filename (default='temp-plot.html') -- The local filename to save the
        outputted chart to. If the filename already exists, it will be
        overwritten. This argument only applies if `output_type` is 'file'.
    auto_open (default=True) -- If True, open the saved file in a
        web browser after saving.
        This argument only applies if `output_type` is 'file'.
    """
    if output_type not in ['div', 'file']:
        raise ValueError(
            "`output_type` argument must be 'div' or 'file'. "
            "You supplied `" + output_type + "``")
    if not filename.endswith('.html') and output_type == 'file':
        warnings.warn(
            "Your filename `" + filename + "` didn't end with .html. "
            "Adding .html to the end of your file.")
        filename += '.html'

    plot_html, plotdivid, width, height = _plot_html(
        figure_or_data, show_link, link_text, validate,
        '100%', '100%', global_requirejs=False)

    resize_script = ''
    if width == '100%' or height == '100%':
        resize_script = (
            ''
            '<script type="text/javascript">'
            'window.removeEventListener("resize");'
            'window.addEventListener("resize", function(){{'
            'Plotly.Plots.resize(document.getElementById("{id}"));}});'
            '</script>'
        ).format(id=plotdivid)

    if output_type == 'file':
        with open(filename, 'w') as f:
            if include_plotlyjs:
                plotly_js_script = ''.join([
                    '<script type="text/javascript">',
                    get_plotlyjs(),
                    '</script>',
                ])
            else:
                plotly_js_script = ''

            f.write(''.join([
                '<html>',
                '<head><meta charset="utf-8" /></head>',
                '<body>',
                plotly_js_script,
                plot_html,
                resize_script,
                '</body>',
                '</html>']))

        url = 'file://' + os.path.abspath(filename)
        if auto_open:
            webbrowser.open(url)

        return url

    elif output_type == 'div':
        if include_plotlyjs:
            return ''.join([
                '<div>',
                '<script type="text/javascript">',
                get_plotlyjs(),
                '</script>',
                plot_html,
                '</div>'
            ])
        else:
            return plot_html


def plot_mpl(mpl_fig, resize=False, strip_style=False,
             verbose=False, show_link=True, link_text='Export to plot.ly',
             validate=True, output_type='file', include_plotlyjs=True,
             filename='temp-plot.html', auto_open=True):
    """
    Convert a matplotlib figure to a Plotly graph stored locally as HTML.

    For more information on converting matplotlib visualizations to plotly
    graphs, call help(plotly.tools.mpl_to_plotly)

    For more information on creating plotly charts locally as an HTML document
    or string, call help(plotly.offline.plot)

    mpl_fig -- a matplotlib figure object to convert to a plotly graph

    Keyword arguments:
    resize (default=False) -- allow plotly to choose the figure size.
    strip_style (default=False) -- allow plotly to choose style options.
    verbose (default=False) -- print message.
    show_link (default=True) -- display a link in the bottom-right corner of
        of the chart that will export the chart to Plotly Cloud or
        Plotly Enterprise
    link_text (default='Export to plot.ly') -- the text of export link
    validate (default=True) -- validate that all of the keys in the figure
        are valid? omit if your version of plotly.js has become outdated
        with your version of graph_reference.json or if you need to include
        extra, unnecessary keys in your figure.
    output_type ('file' | 'div' - default 'file') -- if 'file', then
        the graph is saved as a standalone HTML file and `plot`
        returns None.
        If 'div', then `plot` returns a string that just contains the
        HTML <div> that contains the graph and the script to generate the
        graph.
        Use 'file' if you want to save and view a single graph at a time
        in a standalone HTML file.
        Use 'div' if you are embedding these graphs in an HTML file with
        other graphs or HTML markup, like a HTML report or an website.
    include_plotlyjs (default=True) -- If True, include the plotly.js
        source code in the output file or string.
        Set as False if your HTML file already contains a copy of the plotly.js
        library.
    filename (default='temp-plot.html') -- The local filename to save the
        outputted chart to. If the filename already exists, it will be
        overwritten. This argument only applies if `output_type` is 'file'.
    auto_open (default=True) -- If True, open the saved file in a
        web browser after saving.
        This argument only applies if `output_type` is 'file'.

    Example:
    ```
    from plotly.offline import init_notebook_mode, plot_mpl
    import matplotlib.pyplot as plt

    init_notebook_mode()

    fig = plt.figure()
    x = [10, 15, 20, 25, 30]
    y = [100, 250, 200, 150, 300]
    plt.plot(x, y, "o")

    plot_mpl(fig)
    ```
    """
    plotly_plot = tools.mpl_to_plotly(mpl_fig, resize, strip_style, verbose)
    return plot(plotly_plot, show_link, link_text, validate, output_type,
                include_plotlyjs, filename, auto_open)


def iplot_mpl(mpl_fig, resize=False, strip_style=False,
              verbose=False, show_link=True,
              link_text='Export to plot.ly', validate=True):
    """
    Convert a matplotlib figure to a plotly graph and plot inside an IPython
    notebook without connecting to an external server.

    To save the chart to Plotly Cloud or Plotly Enterprise, use
    `plotly.plotly.plot_mpl`.

    For more information on converting matplotlib visualizations to plotly
    graphs call `help(plotly.tools.mpl_to_plotly)`

    For more information on plotting plotly charts offline in an Ipython
    notebook call `help(plotly.offline.iplot)`

    mpl_fig -- a matplotlib.figure to convert to a plotly graph

    Keyword arguments:
    resize (default=False) -- allow plotly to choose the figure size.
    strip_style (default=False) -- allow plotly to choose style options.
    verbose (default=False) -- print message.
    show_link (default=True) -- display a link in the bottom-right corner of
                                of the chart that will export the chart to
                                Plotly Cloud or Plotly Enterprise
    link_text (default='Export to plot.ly') -- the text of export link
    validate (default=True) -- validate that all of the keys in the figure
                               are valid? omit if your version of plotly.js
                               has become outdated with your version of
                               graph_reference.json or if you need to include
                               extra, unnecessary keys in your figure.

    Example:
    ```
    from plotly.offline import init_notebook_mode, iplot_mpl
    import matplotlib.pyplot as plt

    fig = plt.figure()
    x = [10, 15, 20, 25, 30]
    y = [100, 250, 200, 150, 300]
    plt.plot(x, y, "o")

    init_notebook_mode()
    iplot_mpl(fig)
    ```
    """
    plotly_plot = tools.mpl_to_plotly(mpl_fig, resize, strip_style, verbose)
    return iplot(plotly_plot, show_link, link_text, validate)


def enable_mpl_offline(resize=False, strip_style=False,
                       verbose=False, show_link=True,
                       link_text='Export to plot.ly', validate=True):
    """
    Convert mpl plots to locally hosted HTML documents.

    This function should be used with the inline matplotlib backend
    that ships with IPython that can be enabled with `%pylab inline`
    or `%matplotlib inline`. This works by adding an HTML formatter
    for Figure objects; the existing SVG/PNG formatters will remain
    enabled.

    (idea taken from `mpld3._display.enable_notebook`)

    Example:
    ```
    from plotly.offline import enable_mpl_offline
    import matplotlib.pyplot as plt

    enable_mpl_offline()

    fig = plt.figure()
    x = [10, 15, 20, 25, 30]
    y = [100, 250, 200, 150, 300]
    plt.plot(x, y, "o")
    fig
    ```
    """
    init_notebook_mode()

    ip = IPython.core.getipython.get_ipython()
    formatter = ip.display_formatter.formatters['text/html']
    formatter.for_type(matplotlib.figure.Figure,
                       lambda fig: iplot_mpl(fig, resize, strip_style, verbose,
                                             show_link, link_text, validate))

def download_notebook_image(format='png', height=600, width=800,
                            filename='newplot'):
    """
    Download an image of the most recent plot. This function should be
    called in a cell following the output cell that includes the plot.
    In other words, do not run this functon in the same cell as your
    iplot call.

    Keyword arguments:
    format -- sets the image format for the saved file (default='png')
    Accepts formats include: .jpeg, .png, .svg, .webp
    height -- sets the height of the image in px (default=600)
    width -- sets the width of the image in px (default=800)
    filename -- the name of the saved file without format extension
    (default='newplot')
    """
    script = ('<script>'
              'function downloadimage(format, height, width,'
              ' filename) {{'
              'var elementsList = document.querySelectorAll(\'.code_cell\');'
              'var new_list = new Array();'
              'for(var i=0; i < elementsList.length; i++) {{'
              'if(elementsList[i].classList.contains(\'selected\')) {{'
              'break;'
              '}};'
              'var temp = elementsList[i].getElementsByClassName'
              '(\'plot-container plotly\');'
              'if (temp.length > 0) {{'
              'new_list.push(elementsList[i].getElementsByClassName'
              '(\'plot-container plotly\')[0]);'
              '}}'
              '}}'
              'if (new_list.length>0) {{'
              'var pre_div = new_list.slice(-1)[0];'
              'var p = document.getElementById(pre_div.parentElement.id);'
              'Plotly.downloadImage(p, {{format: format, height: height, '
              'width: width, filename: filename}});'
              '}}'
              '}}'
              'downloadimage(\'{format}\', {height}, {width}, \'{filename}\');'
              '</script>'
              ).format(format=format, height=height, width=width,
                       filename=filename)

    display(HTML(script))
