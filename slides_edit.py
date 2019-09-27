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
from markdown_editor import web_edit
from markdown_editor.editor import MarkdownDocument, write_output, read_input
from markdown_editor.web_edit import WebAction

STYLE_DEFAULT_CONFIG = {u'style_first': [], u'style_default': [], u'styles': {}}


HEADER_TEMPLATE = Template(u"""\
        &nbsp;<span class="glyphicon glyphicon-edit"></span>&nbsp;<span>${name}</span>
        <script>
            var reveal_port = ${reveal_port};
            ${js}
        </script>""")

logger = logging.getLogger('MARKDOWN_EDITOR')

reveal_port = 8424


class RevealMarkdownDocument(MarkdownDocument):

    def __init__(self, styles_config_file, mdtext='', infile=None, outfile=None, md=None):
        MarkdownDocument.__init__(self, mdtext, infile, outfile, md, None, None)
        self.styles_config_file = styles_config_file
        self.slides_data = {'slide_ref': ''}
        self.save(False)

    def get_html(self):
        return u''

    def save(self, input_also=True):
        self.fix_crlf_input_text()

        with codecs.open(self.output_file, 'r', 'utf-8') as f:
            html = f.read()

        with open(self.styles_config_file, 'r') as f:
            try:
                styles_config = json.load(f)
            except ValueError as e:
                styles_config = STYLE_DEFAULT_CONFIG
                raise e
            finally:
                md_out = restore_styles_to_markdown(self.text, styles_config)
                write_output(self.input_file, md_out) if input_also else None
                html_new = self.replace_md_into_html(md_out, html, styles_config)
                write_output(self.output_file, html_new)

        return None, True

    def replace_md_into_html(self, md_out, html, styles_config):
        return re.sub(
            u'(<section.*<script type="text/template">\n).*(\n\t*</script>.*</section>)',
            u'\\1{}\\2'.format(md_out), html, 1, re.DOTALL)


def remove_styles_from_markdown(md_text):
    md_nostyle = re.sub(u'(\n(?:------|---)(?: \.style: .*)?\n)(?:<!--.*-->\n)*', u'\\1', md_text)
    md_nostyle = re.sub(u'^(?:<!--.*\n)*', u'', md_nostyle, 1, re.MULTILINE)
    return md_nostyle


def restore_styles_to_markdown(md_text, styles_config):

    _ = styles_config.get('style_first')
    md_addstyle = u'\n'.join(_) + u'\n' + md_text

    _ = styles_config.get('style_default')
    md_addstyle = re.sub(u'(\n(?:------|---)\n)', '\\1' + u'\n'.join(_ + ['']), md_addstyle)

    _ = styles_config.get('styles')
    for style in _:
        md_addstyle = re.sub(u'(\n(?:------|---) \.style: {}\n)'.format(style), u'\\1' +
                             u'\n'.join(_.get(style) + ['']), md_addstyle)

    return md_addstyle


def extract_markdown_from_section_template(html_file_input):
    with codecs.open(html_file_input, 'r', 'utf-8') as f:
        return re.findall(u'<section.*<script type="text/template">\n(.*)\n\t*</script>.*</section>', f.read(), re.DOTALL)[0]


def action_preview(document):
    return None, u'http://localhost:{}/#/{}'.format(reveal_port, document.slides_data.get('slide_ref'))


def ajax_update_status(document, data):
    document.slides_data = json.loads(data)
    return u'OK'


def main():  # pragma: no cover

    # Parse options and adjust logging level if necessary
    options, logging_level = parse_options()
    if not options: sys.exit(2)
    if not options.get('input'): options['input'] = 'index.md'
    if not options.get('output'): options['output'] = 'index.html'
    logger.setLevel(logging_level)
    logger.addHandler(logging.StreamHandler())

    if not os.path.exists('index.md'):
        md_text = extract_markdown_from_section_template(options['output'])
        write_output('index.md', md_text)

    if not os.path.exists(options['input']):
        md_text = 'Slide1\n------\nSlide2'
    else:
        md_text = read_input(options['input'])

    doc = RevealMarkdownDocument('./slides_edit_styles.json',
                                 mdtext=remove_styles_from_markdown(md_text),
                                 infile=options['input'], outfile=options['output'])

    with open('./slides_edit.js', 'r') as f:
        js_content = f.read()

    npm_start = subprocess.Popen(['npm', 'start', '--', '--port={}'.format(reveal_port)])
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
            ajax_handlers={'update_status': ajax_update_status}
        )
    finally:
        npm_start.terminate()

if __name__ == '__main__':
    main()

