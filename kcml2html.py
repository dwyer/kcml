#!/usr/bin/env python

import os, re, sys

from xml.dom.minidom import parseString


def get_header_level(line):
  if is_header(line):
    return 1 + get_header_level(line[1:-1])
  else:
    return 0


def get_list_text(line):
  if line[0] == ' ' or line[0] == '*' or line[0] == '#':
    return get_list_text(line[1:])
  else:
    return line


def is_header(line):
  return line[0] == line[-1] == '='


def is_list(line):
  return re.match('^\s*[\*|#]\s+', line) != None


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
  # meta charset
  document.head.appendChild(document.createElement('meta'))
  document.head.lastChild.setAttribute('charset', 'utf-8')
  # body
  document.html.appendChild(document.createElement('body'))
  document.body = document.html.lastChild
  return document


def parse(kcml):
  document = create_document()
  parent = document.body
  context = parent
  lines = kcml.splitlines()
  level = 0
  for line in lines:
    if line:
      if is_header(line):
        # when we encounter a header, we must change the section
        header_level = get_header_level(line)
        while level >= header_level:
          parent = parent.parentNode
          level = level - 1
        while level < header_level:
          parent.appendChild(document.createElement('section'))
          parent = parent.lastChild
          level = level + 1
        child = document.createElement('h' + str(level))
        child.appendChild(document.createTextNode(line[level:-level]))
        context = parent
      elif is_list(line): # LISTS!
        list_indent, list_type, item_text = parse_list_item(line)
        child = document.createElement('li')
        child.appendChild(document.createTextNode(item_text))
        if context != parent and context.tagName != list_type:
          context = parent
        if context == parent:
          parent.appendChild(document.createElement(list_type))
          context = parent.lastChild
      else:
        child = document.createTextNode(line)
        if context == parent:
          parent.appendChild(document.createElement('p'))
          context = parent.lastChild
      context.appendChild(child)
    else:
      context = parent
  print document.toprettyxml()


def main(*args):
  for path in args:
    with open(path) as f:
      parse(f.read())
      f.close()


if __name__ == '__main__':
  main(*sys.argv[1:])
