from docutils import nodes
from docutils.io import StringOutput
from sphinx.application import Sphinx
from sphinx.builders.singlehtml import SingleFileHTMLBuilder
from sphinx.environment import BuildEnvironment
from sphinx.util import relative_uri


class SingleFileHTMLBuilderWithoutFinish(SingleFileHTMLBuilder):
    name = 'single_file_html_without_finish'
    format = 'custom'

    def __init__(self, app: Sphinx, env: BuildEnvironment = None) -> None:
        super().__init__(app, env)
        self.init()
        assert self.highlighter is not None
        self.output = None

    def prepare_writing(self, docnames):
        super().prepare_writing(docnames)

    def write_doc(self, docname: str, doctree: nodes.document) -> None:
        # super().write_doc(docname, doctree)
        destination = StringOutput(encoding='utf-8')
        doctree.settings = self.docsettings

        self.secnumbers = self.env.toc_secnumbers.get(docname, {})
        self.fignumbers = self.env.toc_fignumbers.get(docname, {})
        self.imgpath = relative_uri(self.get_target_uri(docname), '_images')
        self.dlpath = relative_uri(self.get_target_uri(docname), '_downloads')
        self.current_docname = docname

        self.docwriter.write(doctree, destination)
        self.docwriter.assemble_parts()

        # WIP: Here we don't do anything else because we already have our
        # HTML content in memory. Builder can simply store it now.
        # body = self.docwriter.parts['fragment']
        # self.output = body

        # ctx = self.get_doc_context(docname, body, metatags)
        # self.handle_page(docname, ctx, event_arg=doctree)

    def finish(self) -> None:
        # WIP: This saves quite a lot of time.
        # super().finish()
        pass
