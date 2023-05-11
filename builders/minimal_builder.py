import logging
from typing import Any, Iterable, Optional, Sequence

from docutils import nodes
from docutils.frontend import OptionParser
from docutils.io import StringOutput
from sphinx.application import Sphinx
from sphinx.builders.singlehtml import SingleFileHTMLBuilder
from sphinx.environment import BuildEnvironment
from sphinx.util import relative_uri
from sphinx.util.console import darkgreen  # type: ignore
from sphinx.util.nodes import inline_all_toctrees
from sphinx.util.parallel import SerialTasks
from sphinx.writers.html import HTMLWriter

# Force Sphinx to produce no logs.
logging.disable(logging.CRITICAL)


class MinimalBuilder(SingleFileHTMLBuilder):
    name = 'minimal'
    format = 'custom'

    def __init__(self, app: Sphinx, env: BuildEnvironment = None) -> None:
        super().__init__(app, env)
        self.init()

        self.doctree = None
        self.indexer = None
        self.output = None
        self.strictdoc_output = None

    def build(
        self, docnames: Iterable[str], summary: Optional[str] = None, method: str = 'update'
    ) -> None:
        updated_docnames = set(self.read())

        if updated_docnames:
            # global actions
            self.env.check_consistency()

        self.parallel_ok = False

        self.finish_tasks = SerialTasks()

        # write all "normal" documents (or everything for some builders)
        self.write(docnames, list(updated_docnames), method)

        # finish (write static files etc.)
        self.finish()

        # wait for all tasks
        self.finish_tasks.join()

    def write(self, build_docnames: Iterable[str], updated_docnames: Sequence[str], method: str = 'update') -> None:  # NOQA
        # super().write(build_docnames, updated_docnames, method)

        docnames = self.env.all_docs
        self.prepare_writing(docnames)  # type: ignore

        # with progress_message(__('assembling single document')):
        # doctree = self.assemble_doctree()
        master = self.config.root_doc
        tree = self.doctree
        tree = inline_all_toctrees(self, set(), master, tree, darkgreen, [master])
        tree['docname'] = master
        self.env.resolve_references(tree, master, self)
        self.fix_refuris(tree)
        doctree = tree

        self.env.toc_secnumbers = self.assemble_toc_secnumbers()
        self.env.toc_fignumbers = self.assemble_toc_fignumbers()

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
        self.secnumbers = self.env.toc_secnumbers.get(docname, {})
        self.fignumbers = self.env.toc_fignumbers.get(docname, {})
        self.imgpath = relative_uri(self.get_target_uri(docname), '_images')
        self.dlpath = relative_uri(self.get_target_uri(docname), '_downloads')
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
