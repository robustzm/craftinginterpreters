#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""

Parses the Java and C source files and separates out their sections. This is
used by both split_chapters.py (to make the chapter-specific source files to
test against) and build.py (to include code sections into the book).

There are a few kinds of section markers:

//> [chapter] [number]

    This marks the following code as being added in snippet [number] in
    [chapter]. A section marked like this must be closed with...

    If this is beginning a new section in the same chapter, the name is omitted.

//< [chapter] [number]

    Ends the previous innermost //> section and returns the whatever section
    surrounded it. The chapter and number are redundant, but are required to
    validate that we're exiting the section we intend to.

/* [chapter] [number] < [end chapter] [end number]
...
*/

    This marks the code in the rest of the block comment as being added in
    section [number] in [chapter]. It is then replaced or removed in section
    [end number] in [end chapter].

    Since this section doesn't end up in the final version of the code, it's
    commented out in the source.

    After the block comment, this returns to the previous section, if any.

"""

import os
import re
import sys

import book

BLOCK_PATTERN = re.compile(r'/\* ([A-Za-z\s]+) (\d+) < ([A-Za-z\s]+) (\d+)')
BLOCK_SECTION_PATTERN = re.compile(r'/\* < (\d+)')
BEGIN_SECTION_PATTERN = re.compile(r'//> (\d+)')
END_SECTION_PATTERN = re.compile(r'//< (\d+)')
BEGIN_CHAPTER_PATTERN = re.compile(r'//> ([A-Za-z\s]+) (\d+)')
END_CHAPTER_PATTERN = re.compile(r'//< ([A-Za-z\s]+) (\d+)')

# Hacky regex that matches a method or function declaration.
FUNCTION_PATTERN = re.compile(r'(\w+)>* (\w+)\(')

# Reserved words that can appear like a return type in a function declaration
# but shouldn't be treated as one.
KEYWORDS = ['new', 'return']

class SourceCode:
  """ All of the source files in the book. """

  def __init__(self):
    self.files = []

    # The chapter/number pairs of every parsed section. Used to ensure we don't
    # try to create the same section twice.
    self.all_sections = {}


  def find_all(self, chapter):
    """ Gets the list of sections that occur in [chapter]. """
    sections = {}

    first_lines = {}
    last_lines = {}

    # Create a new section for [number] if it doesn't already exist.
    def ensure_section(number, line_num):
      if not number in sections:
        section = Section(file, number)
        sections[number] = section
        first_lines[section] = line_num
        return section

      section = sections[number]
      if number != 99 and section.file.path != file.path:
        raise "{} {} appears in two files, {} and {}".format(
            chapter, number, section.file.path, file.path)

      return section

    # TODO: If this is slow, could organize directly by sections in SourceCode.
    # Find the lines added and removed in each section.
    for file in self.files:
      line_num = 0
      for line in file.lines:
        if line.chapter == chapter:
          section = ensure_section(line.number, line_num)
          section.added.append(line.text)
          last_lines[section] = line_num

          if line.function and not section.function:
            section.function = line.function

        if line.end_chapter == chapter:
          section = ensure_section(line.end_number, line_num)
          section.removed.append(line.text)
          last_lines[section] = line_num

        line_num += 1

    if len(sections) == 0: return sections

    # Find the surrounding context lines and location for each section.
    chapter_number = book.chapter_number(chapter)
    for number, section in sections.items():
      # Look for preceding lines.
      i = first_lines[section] - 1
      before = []
      while i >= 0 and len(before) <= 5:
        line = section.file.lines[i]
        if line.is_present(chapter_number, number):
          before.append(line.text)

          if line.function and not section.preceding_function:
            section.preceding_function = line.function
        i -= 1
      section.context_before = before[::-1]

      # Look for following lines.
      i = last_lines[section] + 1
      after = []
      while i < len(section.file.lines) and len(after) <= 5:
        line = section.file.lines[i]
        if line.is_present(chapter_number, number):
          after.append(line.text)
        i += 1
      section.context_after = after

    # if chapter == "Scanning":
    #   for number, section in sections.items():
    #     print("Scanning {} - {}".format(number, section.file.path))
    #     for line in section.context_before:
    #       print("   {}".format(line.rstrip()))
    #     for line in section.removed:
    #       print("-- {}".format(line.rstrip()))
    #     for line in section.added:
    #       print("++ {}".format(line.rstrip()))
    #     for line in section.context_after:
    #       print("   {}".format(line.rstrip()))

    #   for section, first in first_lines.items():
    #     last = last_lines[section]
    #     print("Scanning {} - {}: {} to {}".format(
    #         section.number, section.file.path, first, last))

    return sections

  def split_chapter(self, file, chapter, number):
    """ Gets the code for [file] as it appears at [number] of [chapter]. """
    chapter_number = book.chapter_number(chapter)

    source_file = None
    for source in self.files:
      if source.path == file:
        source_file = source
        break

    if source_file == None:
      raise Exception('Could not find file "{}"'.format(file))

    output = ""
    for line in source_file.lines:
      if (line.is_present(chapter_number, number)):
        # Hack. In generate_ast.java, we split up a parameter list among
        # multiple chapters, which leads to hanging commas in some cases.
        # Remove them.
        if line.text.strip().startswith(")") and output.endswith(",\n"):
          output = output[:-2] + "\n"

        output += line.text + "\n"
    return output


class SourceFile:
  def __init__(self, path):
    self.path = path
    self.lines = []

  def language(self):
    return 'java' if self.path.endswith('java') else 'c'

  def nice_path(self):
    return self.path.replace('com/craftinginterpreters/', '')


class SourceLine:
  def __init__(self, text, function, chapter, number, end_chapter, end_number):
    self.text = text
    self.function = function
    self.chapter = chapter
    self.number = number
    self.end_chapter = end_chapter
    self.end_number = end_number

  def chapter_index(self):
    return book.chapter_number(self.chapter)

  def end_chapter_index(self):
    return book.chapter_number(self.end_chapter)

  def is_present(self, chapter_index, section_number):
    """ If this line exists by [section_number] of [chapter_index]. """
    if chapter_index < self.chapter_index():
      # We haven't gotten to its chapter yet.
      return False
    elif chapter_index == self.chapter_index():
      if section_number < self.number:
        # We haven't reached this section yet.
        return False

    if self.end_chapter != None:
      if chapter_index > self.end_chapter_index():
        # We are past the chapter where it is removed.
        return False
      elif chapter_index == self.end_chapter_index():
        if section_number > self.end_number:
          # We are past this section where it is removed.
          return False

    return True

  def __str__(self):
    result = "{:72} // {} {}".format(self.text, self.chapter, self.number)

    if self.end_chapter:
      result += " < {} {}".format(self.end_chapter, self.end_number)

    if self.function:
      result += " (in {})".format(self.function)

    return result


class Section:
  def __init__(self, file, number):
    self.file = file
    self.number = number
    self.context_before = []
    self.added = []
    self.removed = []
    self.context_after = []

    self.function = None
    self.preceding_function = None

  def location(self):
    """Describes where in the file this section appears."""

    if len(self.context_before) == 0:
      # No lines before the section, it must be a new file.
      return 'create new file'

    if self.function:
      if self.function != self.preceding_function:
        return 'add after <em>{}</em>()'.format(
            self.preceding_function)
      else:
        return 'in <em>{}</em>()'.format(self.function)

    return None


class ParseState:
  def __init__(self, parent, chapter, number, end_chapter=None, end_number=None):
    self.parent = parent
    self.chapter = chapter
    self.number = number
    self.end_chapter = end_chapter
    self.end_number = end_number


def load_file(source_code, source_dir, path):
  relative = os.path.relpath(path, source_dir)

  # Don't process the generated files. We only worry about GenerateAst.java.
  if relative == "com/craftinginterpreters/lox/Expr.java": return
  if relative == "com/craftinginterpreters/lox/Stmt.java": return

  file = SourceFile(relative)
  source_code.files.append(file)

  line_num = 1
  state = ParseState(None, None, None)
  handled = False

  current_function = None

  def fail(message):
    print("{} line {}: {}".format(relative, line_num, message), file=sys.stderr)
    sys.exit(1)

  def push(chapter, number, end_chapter=None, end_number=None):
    nonlocal state
    nonlocal handled

    # 99 is a magic number for sections in chapters that haven't been done yet.
    # Don't worry about duplication.
    # if number != 99:
    #   name = "{} {}".format(chapter, number)
    #   if name in source_code.all_sections:
    #     fail('Duplicate section "{}" is also in {}'.format(name,
    #         source_code.all_sections[name]))
    #   source_code.all_sections[name] = "{} line {}".format(relative, line_num)

    state = ParseState(state, chapter, number, end_chapter, end_number)
    handled = True

  def pop():
    nonlocal state
    nonlocal handled
    state = state.parent
    handled = True

  # Split the source file into chunks.
  with open(path, 'r') as input:
    for line in input:
      line = line.rstrip()
      handled = False

      # See if we reached a new function or method declaration.
      match = FUNCTION_PATTERN.search(line)
      if match and match.group(1) not in KEYWORDS:
        # Hack. Don't get caught by comments or string literals.
        if '//' not in line and '"' not in line:
          current_function = match.group(2)

      match = BLOCK_PATTERN.match(line)
      if match:
        push(match.group(1), int(match.group(2)), match.group(3), int(match.group(4)))

      match = BLOCK_SECTION_PATTERN.match(line)
      if match:
        number = int(match.group(1))
        push(state.chapter, state.number, state.chapter, number)

      if line.strip() == '*/' and state.end_chapter:
        pop()

      match = BEGIN_SECTION_PATTERN.match(line)
      if match:
        number = int(match.group(1))
        if number < state.number:
          fail("Can't push an earlier number {} from {}.".format(number, state.number))
        elif number == state.number:
          fail("Can't push to same number {}.".format(number))
        push(state.chapter, number)

      match = END_SECTION_PATTERN.match(line)
      if match:
        number = int(match.group(1))
        if number != state.number:
          fail("Expecting to pop {} but got {}.".format(state.number, number))
        if state.parent.chapter == None:
          fail('Cannot pop last state "{} {}".'.format(state.chapter, state.number))
        pop()

      match = BEGIN_CHAPTER_PATTERN.match(line)
      if match:
        chapter = match.group(1)
        number = int(match.group(2))

        if state.chapter != None:
          old_chapter = book.chapter_number(state.chapter)
          new_chapter = book.chapter_number(chapter)

          if chapter == state.chapter and number == state.number:
            fail('Pushing same state "{} {}"'.format(chapter, number))
          if chapter == state.chapter:
            fail('Pushing same chapter, just use "//>> {}"'.format(number))
          if new_chapter < old_chapter:
            fail('Can\'t push earlier chapter "{}" from "{}".'.format(
                chapter, state.chapter))
        push(chapter, number)

      match = END_CHAPTER_PATTERN.match(line)
      if match:
        chapter = match.group(1)
        number = int(match.group(2))
        if chapter != state.chapter or number != state.number:
          fail('Expecting to pop "{} {}" but got "{} {}".'.format(
              state.chapter, state.number, chapter, number))
        if state.parent.chapter == None:
          fail('Cannot pop last state "{} {}".'.format(state.chapter, state.number))
        pop()

      if not handled:
        if not state.chapter:
          fail("No section in effect.".format(relative))

        source_line = SourceLine(
            line,
            current_function,
            state.chapter, state.number,
            state.end_chapter, state.end_number)
        file.lines.append(source_line)

      # Hacky. Detect the end of the function. Assumes everything is nicely
      # indented.
      if path.endswith('.java') and line == '  }':
        current_function = None
      elif (path.endswith('.c') or path.endswith('.h')) and line == '}':
        current_function = None

      line_num += 1

    # ".parent.parent" because there is always the top "null" state.
    if state.parent != None and state.parent.parent != None:
      print("{}: Ended with more than one state on the stack.".format(relative), file=sys.stderr)
      s = state
      while s.parent != None:
        print("  {} {}".format(s.chapter, s.number), file=sys.stderr)
        s = s.parent
      sys.exit(1)

  # TODO: Validate that we don't define two sections with the same chapter and
  # number. A section may end up in disjoint lines in the final output because
  # a later section is inserted in it, but it shouldn't be explicitly authored
  # that way.


def load():
  """Creates a new SourceCode object and loads all of the files into it."""
  source_code = SourceCode()

  def walk(dir, extensions, callback):
    dir = os.path.abspath(dir)
    for path in os.listdir(dir):
      nfile = os.path.join(dir, path)
      if os.path.isdir(nfile):
        walk(nfile, extensions, callback)
      elif os.path.splitext(path)[1] in extensions:
        callback(nfile)

  walk("java", [".java"],
      lambda path: load_file(source_code, "java", path))

  walk("c", [".c", ".h"],
      lambda path: load_file(source_code, "c", path))

  return source_code
