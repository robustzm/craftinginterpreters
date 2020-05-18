/// Tracks metadata about the material in the book.
import 'package:path/path.dart' as p;

import 'text.dart';

/*
from functools import total_ordering
import os

# Matches the name in a `^code` tag and ignores the rest.
SNIPPET_TAG_PATTERN = re.compile(r'\s*\^code ([-a-z0-9]+).*')
TITLE_PATTERN = re.compile(r'\^title (.*)')
*/

// TODO: Make private?
// TODO: Make less stringly typed.
const tableOfContents = [
  {
    'name': '',
    'chapters': [
      {
        'name': 'Crafting Interpreters',
      },
      {
        'name': 'Table of Contents',
      }
    ],
  },
  {
    'name': 'Welcome',
    'chapters': [
      {
        'name': 'Introduction',
        'design_note': "What's in a Name?"
      },
      {
        'name': 'A Map of the Territory',
      },
      {
        'name': 'The Lox Language',
        'design_note': "Expressions and Statements"
      }
    ]
  },
  {
    'name': 'A Tree-Walk Interpreter',
    'chapters': [
      {
        'name': 'Scanning',
        'design_note': "Implicit Semicolons"
      },
      {
        'name': 'Representing Code',
      },
      {
        'name': 'Parsing Expressions',
        'design_note': "Logic Versus History"
      },
      {
        'name': 'Evaluating Expressions',
        'design_note': 'Static and Dynamic Typing'
      },
      {
        'name': 'Statements and State',
        'design_note': 'Implicit Variable Declaration'
      },
      {
        'name': 'Control Flow',
        'design_note': 'Spoonfuls of Syntactic Sugar'
      },
      {
        'name': 'Functions',
      },
      {
        'name': 'Resolving and Binding',
      },
      {
        'name': 'Classes',
        'design_note': 'Prototypes and Power'
      },
      {
        'name': 'Inheritance',
      }
    ]
  },
  {
    'name': 'A Bytecode Virtual Machine',
    'chapters': [
      {
        'name': 'Chunks of Bytecode',
        'design_note': 'Test Your Language'
      },
      {
        'name': 'A Virtual Machine',
        'design_note': 'Register-Based Bytecode'
      },
      {
        'name': 'Scanning on Demand',
      },
      {
        'name': 'Compiling Expressions',
        'design_note': "It's Just Parsing"
      },
      {
        'name': 'Types of Values',
      },
      {
        'name': 'Strings',
        'design_note': 'String Encoding'
      },
      {
        'name': 'Hash Tables',
      },
      {
        'name': 'Global Variables',
      },
      {
        'name': 'Local Variables',
      },
      {
        'name': 'Jumping Back and Forth',
        'design_note': 'Considering Goto Harmful'
      },
      {
        'name': 'Calls and Functions',
      },
      {
        'name': 'Closures',
        'design_note': 'Closing Over the Loop Variable'
      },
      {
        'name': 'Garbage Collection',
        'design_note': 'Generational Collectors'
      },
      {
        'name': 'Classes and Instances',
      },
      {
        'name': 'Methods and Initializers',
        'design_note': 'Novelty Budget'
      },
      {
        'name': 'Superclasses',
      },
      {
        'name': 'Optimization',
      }
    ]
  },
  {
    'name': 'Backmatter',
    'chapters': [
      {
        'name': 'Appendix I',
      },
      {
        'name': 'Appendix II',
      }
    ],
  },
];

/// One page (in the HTML sense) of the book.
///
/// Each chapter, part introduction, and backmatter section is a page.
class Page {
  static final all = _flattenPages();

  final String title;
  // TODO: Enum.
  final String type;

  /// The chapter or part number, like "12", "II", or "".
  final String number;

  Page(this.title, this.type, this.number);

  /// The base file path and URI for the page, without any extension.
  String get fileName {
    if (title == "Crafting Interpreters") return "index";
    if (title == "Table of Contents") return "contents";

    // TODO: Is this still needed?
    // Hack. The introduction has a *subheader* named "Challenges" distinct from
    // the challenges section. This function here is also used to generate the
    // anchor names for the links, so handle that one specially so it doesn't
    // collide with the real "Challenges" section.
    if (title == "Challenges") return "challenges_";

    return toFileName(title);
  }

  /// The path to this page's Markdown source file.
  String get markdownPath => p.join("book", "$fileName.md");

  // TODO: Change to "site" when working.
  /// The path to this page's generated HTML file.
  String get htmlPath => p.join("site_dart", "$fileName.html");

  Page get previous => _adjacent(-1);
  Page get next => _adjacent(1);

  /// Flatten the tree of parts and chapters to a single linear list of pages.
  static List<Page> _flattenPages() {
    var pages = <Page>[];

    var partIndex = 1;
    var chapterIndex = 1;
    var inMatter = false;

    for (var part in tableOfContents) {
      // Front- and backmatter have no names, pages, or numbers.
      var partNumber = "";
      inMatter = part["name"] == "" || part["name"] == "Backmatter";
      if (!inMatter) {
        partNumber = roman(partIndex);
        partIndex += 1;
      }

      // There are no part pages for the front- and backmatter.
      if (part["name"] != "") {
        pages.add(Page(part["name"], "Part", partNumber));
      }

      for (var chapter in part["chapters"]) {
        var name = chapter["name"];

        var chapterNumber = "";
        if (inMatter) {
          // Front- and backmatter chapters are specially numbered.
          if (name == "Appendix I") {
            chapterNumber = "A1";
          } else if (name == "Appendix II") {
            chapterNumber = "A2";
          }
        } else {
          chapterNumber = chapterIndex.toString();
          chapterIndex++;
        }

        pages.add(Page(name, "Chapter", chapterNumber));
      }
    }

    return pages;
  }

  /// Gets the [Page] [offset] pages before or after this one.
  Page _adjacent(int offset) {
    var index = all.indexOf(this) + offset;
    if (index < 0 || index >= all.length) return null;
    return all[index];
  }
}

/*
def list_code_chapters():
  """Gets the list of titles of the chapters that have code."""
  chapters = []

  def walk_part(part):
    for chapter in part['chapters']:
      chapters.append(chapter['name'])

  walk_part(TOC[2])
  walk_part(TOC[3])
  walk_part(TOC[4])

  return chapters

CODE_CHAPTERS = list_code_chapters()


def adjacent_type(title, offset):
  '''Generate template data to link to the previous or next page.'''
  page_index = PAGES.index(title) + offset
  if page_index < 0 or page_index >= len(PAGES): return None

  return TYPES[page_index]


def chapter_number(name):
  """
  Given the name of a chapter (or part of end matter page), finds its number.
  """
  if name in NUMBERS:
    return NUMBERS[name]

  # The chapter has no number. This is true for the appendices.
  return ""


def get_language(name):
  if CODE_CHAPTERS.index(name) < CODE_CHAPTERS.index("Chunks of Bytecode"):
    return "java"
  return "c"


def get_short_name(name):
  number = chapter_number(name)

  first_word = name.split()[0].lower().replace(',', '')
  if first_word == "a" or first_word == "the":
    first_word = name.split()[1].lower()
  if first_word == "user-defined":
    first_word = "user"

  return "chap{0:02d}_{1}".format(number, first_word)


@total_ordering
class SnippetTag:
  def __init__(self, chapter, name, index):
    self.chapter = chapter
    self.name = name
    self.chapter_index = chapter_number(chapter)
    self.index = index

    # Hackish. Always want "not-yet" to be the last tag even if it appears
    # before a real tag. That ensures we can push it for other tags that have
    # been named.
    if name == "not-yet":
      self.index = 9999

  def __eq__(self, other):
      return (isinstance(other, SnippetTag) and
          self.chapter_index == other.chapter_index and
          self.index < other.index)

  def __lt__(self, other):
    if self.chapter_index != other.chapter_index:
      return self.chapter_index < other.chapter_index

    return self.index < other.index

  def __repr__(self):
    return "Tag({}|{}: {} {})".format(
        self.chapter_index, self.index, self.chapter, self.name)


def get_chapter_snippet_tags():
  """
  Parses the snippet tags from every chapter. Returns a map of chapter names
  to maps of snippet names to SnippetTags.
  """
  chapters = {}

  for chapter in CODE_CHAPTERS:
    chapters[chapter] = get_snippet_tags(get_markdown_path(chapter))

  # for chapter, tags in chapters.items():
  #   print(chapter)
  #   for tag in tags.values():
  #     print("  {}".format(tag))

  return chapters


def get_snippet_tags(path):
  """
  Parses the Markdown file at [path] and finds all of the `^code` tags.
  Returns a map of snippet names to SnippetTags for them.
  """
  tags = {}

  with open(path, 'r') as input:
    title = None

    for line in input:
      match = TITLE_PATTERN.match(line)
      if match:
        title = match.group(1)

      match = SNIPPET_TAG_PATTERN.match(line)
      if match:
        if title == None:
          raise Exception("Should have found title first.")
        tags[match.group(1)] = SnippetTag(title, match.group(1), len(tags))

  return tags

*/