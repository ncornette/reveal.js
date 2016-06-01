#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import logging
import codecs
import json
from string import Template
from markdown_edit import editor
import subprocess
from functools import partial

logger = logging.getLogger('MARKDOWN_EDITOR')

def markdown_in(md_text):
    md_nostyle = re.sub('(\n(?:------|---) \.style: .*\n)(?:<!--.*-->\n)*', '\\1', md_text)
    md_nostyle = re.sub('^(?:<!--.*\n)*', '', md_nostyle, 1, re.MULTILINE)
    return md_nostyle

def markdown_out(md_text, config):
    md_addstyle = '\n'.join(config.get('style_first')) + '\n' + md_text

    md_addstyle = re.sub('(\n(?:------|---)\n)', '\\1' + '\n'.join(config.get('style_default') + ['']), md_addstyle)

    for style in config.get('styles'):
        md_addstyle = re.sub('(\n(?:------|---) .style: {}\n)'.format(style), '\\1' + '\n'.join(config.get('styles').get(style) + ['']), md_addstyle)

    return md_addstyle

def get_markdown(html_file_input):
    with codecs.open(html_file_input, 'r', 'utf-8') as f:
        md_text = re.findall(r'<section.*<script type="text/template">\n(.*)\n\t*</script>.*</section>', f.read(), re.DOTALL)[0]
        return markdown_in(md_text)

def action_save(config, document):
    document.fix_crlf_input_text()

    with codecs.open(document.input_file, 'r', 'utf-8') as f:
        html = f.read()

    with open(config, 'r') as f:
        try:
            config = json.load(f)
        except ValueError as e:
            config = {"style_first": [], "style_default": [], "styles": {}}
            raise e
        finally:
            html_new = re.sub(r'(<section.*<script type="text/template">\n).*(\n\t*</script>.*</section>)', ur'\1{}\2'.format(markdown_out(document.text, config)), html, 1, re.DOTALL)
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

    editor.action_save = partial(action_save, './slides_edit_styles.json')

    editor.web_edit(
        doc, 
        port=options['port'], 
        title=HEADER_TEMPLATE.substitute(name=input_basename, js=js_content)
    )
    
    npm_start.terminate()

if __name__ == '__main__':
    main()

