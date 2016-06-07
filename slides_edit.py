#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import logging
import codecs
import json
from string import Template
import subprocess

import sys

from markdown_edit import parse_options
from markdown_editor import editor, web_edit
from markdown_editor.editor import MarkdownDocument, Action
from markdown_editor.web_edit import WebAction

logger = logging.getLogger('MARKDOWN_EDITOR')

reveal_port = 8424


class RevealMarkdownDocument(MarkdownDocument):

    def __init__(self, config_file, mdtext='', infile=None, outfile=None, md=None):
        MarkdownDocument.__init__(self, mdtext, infile, outfile, md, None, None)
        self.config_file = config_file
        self.slides_data = {'slide_ref': ''}

    def get_html(self):
        return u''

    def save(self):
        self.fix_crlf_input_text()

        with codecs.open(self.input_file, 'r', 'utf-8') as f:
            html = f.read()

        with open(self.config_file, 'r') as f:
            try:
                config = json.load(f)
            except ValueError as e:
                config = {u'style_first': [], u'style_default': [], u'styles': {}}
                raise e
            finally:
                html_new = re.sub(u'(<section.*<script type="text/template">\n).*(\n\t*</script>.*</section>)', u'\\1{}\\2'.format(markdown_out(self.text, config)), html, 1, re.DOTALL)
                if self.input_file:
                    editor.write_output(self.input_file, html_new)

        return None, True


def markdown_in(md_text):
    md_nostyle = re.sub(u'(\n(?:------|---)(?: \.style: .*)?\n)(?:<!--.*-->\n)*', u'\\1', md_text)
    md_nostyle = re.sub(u'^(?:<!--.*\n)*', u'', md_nostyle, 1, re.MULTILINE)
    return md_nostyle


def markdown_out(md_text, config):
    md_addstyle = u'\n'.join(config.get('style_first')) + u'\n' + md_text

    md_addstyle = re.sub(u'(\n(?:------|---)\n)', '\\1' + u'\n'.join(config.get('style_default') + ['']), md_addstyle)

    for style in config.get('styles'):
        md_addstyle = re.sub(u'(\n(?:------|---) \.style: {}\n)'.format(style), u'\\1' + u'\n'.join(config.get('styles').get(style) + ['']), md_addstyle)

    return md_addstyle


def get_markdown(html_file_input):
    with codecs.open(html_file_input, 'r', 'utf-8') as f:
        md_text = re.findall(u'<section.*<script type="text/template">\n(.*)\n\t*</script>.*</section>', f.read(), re.DOTALL)[0]
        return markdown_in(md_text)


def action_preview(document):
    return None, u'http://localhost:{}/#/{}'.format(reveal_port, document.slides_data.get('slide_ref'))


def ajax_update_status(document, data):
    document.slides_data = json.loads(data)
    return u'OK'


def main():  # pragma: no cover

    # Parse options and adjust logging level if necessary
    options, logging_level = parse_options()
    if not options: sys.exit(2)
    if not options.get('input'): options['input'] = 'index.html'
    logger.setLevel(logging_level)
    logger.addHandler(logging.StreamHandler())

    HEADER_TEMPLATE = Template(u"""\
        &nbsp;<span class="glyphicon glyphicon-edit"></span>&nbsp;<span>${name}</span>
        <script>
            var reveal_port = ${reveal_port};
            ${js}
        </script>""")

    doc = RevealMarkdownDocument('./slides_edit_styles.json',
                                 mdtext=get_markdown(options['input']),
                                 infile=options['input'], outfile=options['output'])

    with open('./slides_edit.js', 'r') as f:
        js_content = f.read()

    npm_start = subprocess.Popen(['npm', 'start', '--', '--port', str(reveal_port)])
    import time; time.sleep(1)  # wait for reveal
    
    input_basename = os.path.basename(doc.input_file)

    web_edit.action_preview = action_preview

    try:
        web_edit.start(
            doc, [WebAction('Print', lambda d: (None, 'http://localhost:{}/?print-pdf'.format(reveal_port)))],
            port=options['port'], 
            title=HEADER_TEMPLATE.substitute(
                name=input_basename, 
                reveal_port=reveal_port, 
                js=js_content),
            ajax_handlers={'ajaxUpdateStatus': ajax_update_status}
        )
    finally:
        npm_start.terminate()

if __name__ == '__main__':
    main()

