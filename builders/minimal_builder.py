import codecs
import logging
import time
from os import path
from typing import Any, Iterable, Optional, Sequence, List

import docutils
from docutils import nodes
from docutils.core import Publisher
from docutils.frontend import OptionParser
from docutils.io import StringOutput, NullOutput
from docutils.utils import DependencyList
from sphinx.application import Sphinx
from sphinx.builders.html import StandaloneHTMLBuilder
from sphinx.builders.singlehtml import SingleFileHTMLBuilder
from sphinx.environment import BuildEnvironment
from sphinx.io import SphinxStandaloneReader, SphinxDummyWriter, SphinxFileInput
from sphinx.util import relative_uri, rst, get_filetype, UnicodeDecodeErrorHandler
from sphinx.util.console import darkgreen  # type: ignore
from sphinx.util.docutils import sphinx_domains
from sphinx.util.nodes import inline_all_toctrees
from sphinx.util.parallel import SerialTasks
from sphinx.writers.html import HTMLWriter


class MyRSTInputReader:
    def __init__(self, input_rst):
        self.input_rst = input_rst

    def read(self):
        return self.input_rst

    def close(self):
        pass


class MinimalBuilder(StandaloneHTMLBuilder):
    name = 'minimal'
    format = 'custom'

    def __init__(self, app: Sphinx, env: BuildEnvironment = None) -> None:
        super().__init__(app, env)
        self.init()

        self.doctree = None
        self.indexer = None
        self.output = None
        self.strictdoc_input = None
        self.strictdoc_output = None

    def build(
        self, docnames: Iterable[str], summary: Optional[str] = None, method: str = 'update'
    ) -> None:
        self.read()

        # write all "normal" documents (or everything for some builders)
        self.write(docnames, list(), method)

    def read(self) -> List[str]:
        """(Re-)read all files new or changed since last update.
        Store all environment docnames in the canonical format (ie using SEP as
        a separator in place of os.path.sep).
        """

        self._read_serial([])

        return []

    def _read_serial(self, docnames: List[str]) -> None:
        self.read_doc("index")

    @staticmethod
    def create_publisher(app: "Sphinx", filetype: str) -> Publisher:
        reader = SphinxStandaloneReader()
        reader.setup(app)

        parser = app.registry.create_source_parser(app, filetype)

        pub = Publisher(
            reader=reader,
            parser=parser,
            writer=SphinxDummyWriter(),
            source_class=SphinxFileInput,
            destination=NullOutput()
        )
        # Propagate exceptions by default when used programmatically:
        defaults = {"traceback": True, **app.env.settings}
        # Set default settings
        pub.get_settings(**defaults)  # type: ignore[arg-type]
        return pub

    def read_doc(self, docname: str) -> None:
        # super().read_doc(docname)

        """Parse a file and add/update inventory entries for the doctree."""
        self.env.prepare_settings(docname)

        filename = self.env.doc2path(docname)
        publisher = MinimalBuilder.create_publisher(self.app, "restructuredtext")

        with sphinx_domains(self.env), rst.default_role(docname, self.config.default_role):
            # set up error_handler for the target document
            codecs.register_error('sphinx', UnicodeDecodeErrorHandler(docname))  # type: ignore

            my_rst_input_reader = MyRSTInputReader(self.strictdoc_input)
            publisher.set_source(
                source=my_rst_input_reader, source_path=filename
            )
            publisher.publish()
            doctree = publisher.document

        # cleanup
        self.env.temp_data.clear()
        self.env.ref_context.clear()

        self.write_doctree(docname, doctree)

    def write(self, build_docnames: Iterable[str], updated_docnames: Sequence[str], method: str = 'update') -> None:  # NOQA
        # super().write(build_docnames, updated_docnames, method)

        docnames = self.env.all_docs
        self.prepare_writing(docnames)  # type: ignore

        # with progress_message(__('assembling single document')):
        # doctree = self.assemble_doctree()
        master = self.config.root_doc
        tree = self.doctree
        # tree = inline_all_toctrees(self, set(), master, tree, darkgreen, [master])
        tree['docname'] = master
        self.env.resolve_references(tree, master, self)
        # self.fix_refuris(tree)
        doctree = tree

        # self.env.toc_secnumbers = self.assemble_toc_secnumbers()
        # self.env.toc_fignumbers = self.assemble_toc_fignumbers()

        # self.write_doc_serialized(self.config.root_doc, doctree)
        self.write_doc(self.config.root_doc, doctree)

        # docnames.add(self.config.root_doc)
        #
        # self.prepare_writing(docnames)
        #
        # for docname in docnames:
        #     assert self.doctree is not None
        #     doctree = self.doctree
        #     # self.write_doc_serialized(docname, doctree)
        #     self.write_doc(docname, doctree)

    def prepare_writing(self, docnames):
        # super().prepare_writing(docnames)

        self.docwriter = HTMLWriter(self)
        self.docsettings: Any = OptionParser(
            defaults=self.env.settings,
            components=(self.docwriter,),
            read_config_files=True).get_default_values()

    def write_doctree(self, docname: str, doctree: nodes.document) -> None:
        # WIP: Instead of writing doctree to pickle, we just store it to memory.
        self.doctree = doctree

    def write_doc(self, docname: str, doctree: nodes.document) -> None:
        # super().write_doc(docname, doctree)
        destination = StringOutput(encoding='utf-8')
        doctree.settings = self.docsettings
        #
        # self.secnumbers = self.env.toc_secnumbers.get(docname, {})
        # self.fignumbers = self.env.toc_fignumbers.get(docname, {})
        # self.imgpath = relative_uri(self.get_target_uri(docname), '_images')
        # self.dlpath = relative_uri(self.get_target_uri(docname), '_downloads')
        self.current_docname = docname
        #
        self.docwriter.write(doctree, destination)
        self.docwriter.assemble_parts()
        body = self.docwriter.parts['fragment']
        self.strictdoc_output = body

        # metatags = self.docwriter.clean_meta
        # assert 0, body
        # self.output = body
        # ctx = self.get_doc_context(docname, body, metatags)
        # self.handle_page(docname, ctx, event_arg=doctree)

    def finish(self) -> None:
        # super().finish()
        pass
