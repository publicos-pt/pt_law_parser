[![Build Status](https://travis-ci.org/publicos-pt/pt_law_parser.svg?branch=master)](https://travis-ci.org/publicos-pt/pt_law_parser)
[![Coverage Status](https://coveralls.io/repos/publicos-pt/pt_law_parser/badge.svg?branch=master)](https://coveralls.io/r/publicos-pt/pt_law_parser?branch=master)

# Portuguese law parser

Interprets texts of the portuguese law. It is written in Python, and depends on
a downloader to retrieve the law.

## What it does:

1. Identifies references to other laws;
2. Identifies references to European laws;
3. Identifies sections and other topographic features of the text

This is done using a combination of a tokenizer, a parser and an analyser.

## Install

     git clone git+https://github.com/publicos-pt/pt_law_parser.git
     pip install -r requirements.txt
     mkdir cached_html

## Test

     python -m unittest discover
