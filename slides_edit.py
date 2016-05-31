#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import logging
import codecs
from string import Template
from markdown_edit import editor
import subprocess

logger = logging.getLogger('MARKDOWN_EDITOR')

def get_markdown(html_file_input):
    with codecs.open(html_file_input, 'r', 'utf-8') as f:
        return re.findall(r'<section.*<script type="text/template">\n(.*)\n\t*</script>.*</section>', f.read(), re.DOTALL)[0]

def action_save(document):
    document.fix_crlf_input_text()

    with codecs.open(document.input_file, 'r', 'utf-8') as f:
        html = f.read()

    html_new = re.sub(r'(<section.*<script type="text/template">\n).*(\n\t*</script>.*</section>)', ur'\1{}\2'.format(document.text), html, 1, re.DOTALL)

    if document.input_file:
        editor.write_output(document.input_file, html_new)

    return None, True

def main():  # pragma: no cover

    # Parse options and adjust logging level if necessary
    options, logging_level = editor.parse_options()
    if not options: sys.exit(2)
    logger.setLevel(logging_level)
    logger.addHandler(logging.StreamHandler())

    HEADER_TEMPLATE = Template(u"""\
        &nbsp;<span class="glyphicon glyphicon-edit"></span>&nbsp;<span>${name}</span>
        <script>${js}</script>"""
    )

    doc = editor.MarkdownDocument(mdtext=get_markdown(options['input']), infile=options['input'], outfile=options['output'])

    with open('./slides_edit.js', 'r') as f:
        js_content = f.read()

    npm_start = subprocess.Popen(['npm', 'start', '--', '--port', '8424'])
    import time; time.sleep(1) # wait for reveal
    
    input_basename = os.path.basename(doc.input_file)

    editor.action_save = action_save

    editor.web_edit(
        doc, 
        port=options['port'], 
        title=HEADER_TEMPLATE.substitute(name=input_basename, js=js_content)
    )
    
    npm_start.terminate()

if __name__ == '__main__':
    main()

