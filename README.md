[![Build Status](https://travis-ci.org/publicos-pt/pt_law_parser.svg?branch=master)](https://travis-ci.org/publicos-pt/pt_law_parser)
[![Coverage Status](https://coveralls.io/repos/publicos-pt/pt_law_parser/badge.svg?branch=master)](https://coveralls.io/r/publicos-pt/pt_law_parser?branch=master)

# Portuguese law parser

This package aims to machine-read the portuguese law officially published in
[dre](http://dre.pt). Thanks for checking it out.

## What this package does:

Allows to tokenize, parse and analyse the raw text from the official source, which 
is downloaded by its dependency [pt_law_downloader](https://github.com/publicos-pt/pt_law_downloader).

In particular, this package structures the text according to the structure of the
law, identifies references to other documents and to European law, and other
perks.

Take a look at the tests to understand how you can use this package. 

## Install

     git clone git+https://github.com/publicos-pt/pt_law_parser.git
     pip install -r requirements.txt
     mkdir cached_html

## Test

     python -m unittest discover
