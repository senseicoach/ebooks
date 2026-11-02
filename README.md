# Free Ebooks by Ron Taylor

Download page: **https://executiveclass.ca/ebooks/**

Every book is free. Each book has its own page, e.g. `https://executiveclass.ca/ebooks/wise-up/`.

## Adding a book
1. Put the `.epub` in `books/` and its cover (JPG) in `covers/`, both with the same name, e.g. `my-book.epub` and `my-book.jpg`.
2. Make the PDF from the EPUB: `pip install weasyprint`, then `python3 tools/epub_to_pdf.py books/my-book.epub books/my-book.pdf`. Open the PDF and check the cover, title page and a few chapters.
3. Add one line for it to the `BOOKS` list near the bottom of `index.html` (any `kb:` / `pkb:` numbers are refreshed in the next step).
4. Run `python3 tools/build_book_pages.py` to create its single-book page and update the file sizes on the buttons.

Every book is offered as both a PDF (opens anywhere) and an EPUB (adjusts to phone and e-reader screens). Always regenerate the PDF whenever you change an EPUB.

## Call to action under the download button
Each book page shows a short message and an "Explore Executive Class" button. The text lives in `tools/build_book_pages.py`:
- `OPENING`: the first sentence, one per book (add one when you add a book).
- `CTA_REST`: the second sentence and button, shared by all books in English or Portuguese.
After editing, run `python3 tools/build_book_pages.py` again.
