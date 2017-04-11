# Catalog Web App

## About
This project provides a catalog database interface to create, read, update, and delete catalog items from different categories.

## To Run
- This project requires the database to be set up.  To do this, run `python cdb_setup.py` in the project folder.

- If you are using vagrant to host this webserver and database, run `vagrant up` in the project folder, and `vagrant ssh` once that completes to connect to the virtual machine.

Now you can start the webserver by running `python server.py`


## Future Additions
* Refactor infrastructure to where item pages are more loosely tied to categories.
  - New item selection has a "Category" drop down box, instead of being accessed from the category itself.
  - Item view, edit, and delete pages not tied to the category page or category ID.

* Add reviews to items.

* Consider refactoring so that there is no category add or delete page.  Categories should be added only when an item is added and no category exists for it yet.
  - If a category matches the text input, DO NOT add new category.  Else, Add new category.
  - After an item is deleted, check if the category that item was in is empty.  If so, delete it.
