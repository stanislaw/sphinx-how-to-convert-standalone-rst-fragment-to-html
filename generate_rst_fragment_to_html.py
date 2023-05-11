import logging
import os
import shutil
import sys
import time

from breathe import setup
from sphinx.application import Sphinx

from builders.minimal_builder import MinimalBuilder
from builders.single_file_html_without_finish import \
    SingleFileHTMLBuilderWithoutFinish

# Force Sphinx to produce no logs.
logging.disable(logging.CRITICAL)


def rst_to_html(path_to_rst_tree, path_to_build, selected_builder):
    srcdir = path_to_rst_tree
    outdir = os.path.join(path_to_build, "sphinx_html")
    doctreedir = os.path.join(path_to_build, "doctrees")

    if os.path.exists(doctreedir):
        shutil.rmtree(doctreedir)
    if os.path.exists(outdir):
        shutil.rmtree(outdir)

    confoverrides = {}
    confoverrides["html_theme"] = "my_theme"
    confoverrides["html_theme_path"] = ["themes"]

    # Initialize and build the Sphinx application
    app = Sphinx(
        srcdir=srcdir,
        confdir=None,
        outdir=outdir,
        doctreedir=doctreedir,
        confoverrides=confoverrides,
        buildername="singlehtml"
    )

    # Register builder.
    if selected_builder == "single_file_html_without_finish":
        builder = SingleFileHTMLBuilderWithoutFinish(app, app.env)
        builder.use_index = False
        app.registry.builders["single_file_html_without_finish"] = builder
        app.builder = app.registry.builders["single_file_html_without_finish"]
    elif selected_builder == "minimal":
        builder = MinimalBuilder(app, app.env)
        builder.use_index = False
        app.registry.builders["minimal"] = builder
        app.builder = app.registry.builders["minimal"]
    elif selected_builder == "single_file_html":
        # Do nothing: We are already using the native singlehtml builder.
        pass
    else:
        raise NotImplementedError

    app.config.breathe_projects = {"DO-178C": "_xml"}
    app.config.html_sidebars = {
        '**': [],
    }

    setup(app=app)

    start_time = time.perf_counter()

    for i in range(1):
        if os.path.exists(doctreedir):
            shutil.rmtree(doctreedir)
        if os.path.exists(outdir):
            shutil.rmtree(outdir)

        app.build(force_all=False)

    end_time = time.perf_counter()
    execution_time = end_time - start_time
    print(f"The execution time is: {execution_time}")


assert len(sys.argv) == 4

builder = sys.argv[1]
assert builder in ["single_file_html", "single_file_html_without_finish", "minimal"]

program_name = sys.argv[0]
path_to_rst_tree = sys.argv[2]
assert os.path.isdir(path_to_rst_tree)

path_to_build = sys.argv[3]

rst_to_html(path_to_rst_tree, path_to_build, builder)
