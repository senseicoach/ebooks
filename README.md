# Free Ebooks by Ron Taylor

Download page: **https://executiveclass.ca/ebooks/**

Every book is free. Each book has its own page, e.g. `https://executiveclass.ca/ebooks/wise-up/`.

## Adding a book
1. Put the `.epub` in `books/` and its cover (JPG) in `covers/`, both with the same name, e.g. `my-book.epub` and `my-book.jpg`.
2. Add one line for it to the `BOOKS` list near the bottom of `index.html`.
3. Run `python3 tools/build_book_pages.py` to create its single-book page.

## Call to action under the download button
Each book page shows a short message and an "Explore Executive Class" button. The text lives in `tools/build_book_pages.py`:
- `OPENING`: the first sentence, one per book (add one when you add a book).
- `CTA_REST`: the second sentence and button, shared by all books in English or Portuguese.
After editing, run `python3 tools/build_book_pages.py` again.
