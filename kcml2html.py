#!/usr/bin/env python

import os, re, sys

from xml.dom.minidom import parseString


META_TAGS = ['author', 'description', 'keywords']
LINK_RELS = ['icon', 'stylesheet']
SECTION_TAGS = ['body', 'section']
HEADER_TAGS = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']
LIST_TAGS = ['ol', 'ul']
ITEM_TAG = 'li'


def is_header(line):
  return line[0] == line[-1] == '='


def is_list(line):
  return re.match('^\s*[\*|#]\s+', line) != None


def parse_header(line, level=0):
  if is_header(line):
    return parse_header(line[1:-1], level+1)
  else:
    return level, 'h%d' % level, line


def parse_list_item(line):
  m = re.match('^(\s*)(\*|#)\s+(.*)$', line)
  a, b, c = m.groups()
  return len(a), {'*': 'ul', '#': 'ol'}[b], c


def create_document():
  document = parseString('<html/>')
  document.html = document.lastChild
  # head
  document.html.appendChild(document.createElement('head'))
  document.head = document.html.lastChild
  # body
  document.html.appendChild(document.createElement('body'))
  document.body = document.html.lastChild
  return document


def create_and_append_element(document, parent, tagName, text=None):
  if tagName == 'section' and parent.tagName not in SECTION_TAGS:
    raise Exception, '<section> tag must belong to <body> or <section>'
  elif tagName in HEADER_TAGS and parent.tagName != 'section':
    raise Exception, '<h*> tags must belong to <section>'
  elif tagName in LIST_TAGS and parent.tagName not in SECTION_TAGS + [ITEM_TAG]:
    raise Exception, 'list elements must belong to a list or section'
  elif tagName == ITEM_TAG and parent.tagName not in LIST_TAGS:
    raise Exception, '<li> tags must belong to <ol> or <ul>'
  parent.appendChild(document.createElement(tagName))
  if text:
    parent.lastChild.appendChild(document.createTextNode(text))


def parse_kcml(kcml, indent=2):
  document = create_document()
  lines = kcml.splitlines()
  _process_head(document, lines)
  _process_body(document, lines)
  xml = document.toprettyxml(indent=' '*indent) if indent else document.toxml()
  html = xml.replace('<?xml version="1.0" ?>', '<!DOCTYPE html>')
  html = re.sub('\[(\S+) (.*?)\]', r'<a href="\1">\2</a>', html)
  html = re.sub('_(.*?)_', r'<i>\1</i>', html)
  return html


def _process_head(document, lines):
  pragmas = {}
  while lines:
    m = re.match('#(\S+)\s(.*)', lines[0])
    if m:
      key, value = m.groups()
      pragmas[key] = value
    else:
      break
    lines.pop(0)
  # meta charset is required
  charset = pragmas.get('charset', 'utf-8')
  document.head.appendChild(document.createElement('meta'))
  document.head.lastChild.setAttribute('charset', charset)
  # title is required
  title = pragmas.get('title', 'Unknown')
  document.head.appendChild(document.createElement('title'))
  document.head.lastChild.appendChild(document.createTextNode(title))
  # handle supported meta tags
  for name in META_TAGS:
    if name in pragmas:
      document.head.appendChild(document.createElement('meta'))
      document.head.lastChild.setAttribute('name', name)
      document.head.lastChild.setAttribute('content', pragmas[name])
  # handle supported link relations
  for rel in LINK_RELS:
    if rel in pragmas:
      document.head.appendChild(document.createElement('link'))
      document.head.lastChild.setAttribute('rel', rel)
      document.head.lastChild.setAttribute('href', pragmas[rel])


def _process_body(document, lines):
  section = document.body
  context = section
  level = 0
  for line in lines:
    if line:
      if is_header(line):
        # when we encounter a header, we must change the section
        header_level, header_type, header_text = parse_header(line)
        while level >= header_level:
          section = section.parentNode
          level = level - 1
        while level < header_level:
          create_and_append_element(document, section, 'section')
          section = section.lastChild
          level = level + 1
        create_and_append_element(document, section, header_type, header_text)
        context = section
      elif is_list(line): # LISTS!
        list_indent, list_type, item_text = parse_list_item(line)
        """IF we're in a higher list, get the hell out!
           make sure we're in the body, a section, or a list"""
        while ((context.tagName not in LIST_TAGS + SECTION_TAGS) or
               (context.tagName in LIST_TAGS and context.indent > list_indent)):
          context = context.parentNode
        """IF we're in a lower list, get in the last item"""
        if context.tagName in LIST_TAGS and context.indent < list_indent:
          context = context.lastChild
        """IF we're in a section OR a list item, create a new list"""
        if context.tagName in SECTION_TAGS or context.tagName == 'li':
          create_and_append_element(document, context, list_type)
          context = context.lastChild
          context.indent = list_indent
        create_and_append_element(document, context, 'li', item_text)
      else:
        child = document.createTextNode(line)
        if context == section:
          section.appendChild(document.createElement('p'))
          context = section.lastChild
        context.appendChild(child)
    else:
      context = section


def main(*args):
  for path in args:
    with open(path) as f:
      html = parse_kcml(f.read())
      print html
      f.close()


if __name__ == '__main__':
  main(*sys.argv[1:])
