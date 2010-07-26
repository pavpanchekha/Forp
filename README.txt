The Forp Programming Language
=============================

Forp is a new programming language whose goal is to maximize program
maintainability and readability. Forp is a language that struggles to
create readable programs that are understandable with as little
background as possible, from a simple syntax to providing powerful
abstractions to allow common patterns to be encapsulated into easy to
describe units.

Forp also maintains a focus on *informality, simplicity, and
dynamicity*. Forp is Lisp- and Python-inspired --- in particular, the
core is Lispish, the syntax is highly Pythonic, and the ideas are a meld
of the two.

For more, please visit the `Forp homepage
<http://panchekha.no-ip.com:8082/forp>`_.

Implementation
--------------

In this distribution are two folders: ``compiler`` and ``vm``. The ``vm``
folder contains the Forp runtime, written in Haskell (for speed and ease). The
``compiler`` folder contains the Forp compiler, written in Python (for ease).
It is expected that Forp will eventually be ported to the .NET/Mono runtime for
added speed and to reduce the burden of supporting our own runtime; once this
happens, the ``vm`` folder will disappear.

Currently, the ``vm`` folder is entirely empty and the ``compiler`` folder
contains only a very incomplete compiler --- only the parser is complete.
