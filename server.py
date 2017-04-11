"""
Catalog Server.

This module runs the server for the Catalog web app.  The Catalog web app is
used to manage a catalog of items.
"""

from flask import \
    Flask, request  # , render_template, redirect, url_for, jsonify, flash

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Create app
app = Flask(__name__)

# Create DB session
engine = create_engine('sqlite:///catalog.db')
DBSession = sessionmaker(bind=engine)
session = DBSession()


# Authorization routing
@app.route('/login')
def showLogin():
    """Show the login page."""
    return "Show Login Page"


# App routing
@app.route('/')
@app.route('/catalog')
def showCatalog():
    """Show the front page of the catalog app."""
    return "Get for Show Catalog"


@app.route('/catalog/JSON')
def showCatalogJSON():
    """Show the Catalog in JSON."""
    return "Show JSON Catalog"


@app.route('/catalog/new', methods=['GET', 'POST'])
def newCategory():
    """Handle the addition of new categories."""
    if request.method == 'POST':
        return "Post for New Category"
    else:
        return "Get for New Category"


@app.route('/catalog/<int:category_id>/edit', methods=['GET', 'POST'])
def editCategory(category_id):
    """Handle the editing of existing categories."""
    if request.method == 'POST':
        return "Post for Edit Category"
    else:
        return "Get for Edit Category"


@app.route('/catalog/<int:category_id>/delete', methods=['GET', 'POST'])
def deleteCategory(category_id):
    """Handle the deletion of categories."""
    if request.method == 'POST':
        return "Post for Delete Category"
    else:
        return "Get for Delete Category"


@app.route('/catalog/<int:category_id>')
@app.route('/catalog/<int:category_id>/menu')
def showCategory(category_id):
    """Show all items in a category."""
    return "Get for show category."


@app.route('/catalog/<int:category_id>/menu/JSON')
def showCategoryJSON(category_id):
    """Show all items in a category in JSON format."""
    # menu = getMenu(restaurant_id)
    # return jsonify(Menu=[m.serialize for m in menu])


@app.route('/catalog/<int:category_id>/menu/new', methods=['GET', 'POST'])
def newItem(category_id):
    """Handle the addition of new catalog items."""
    if request.method == 'POST':
        return "Post for New Item"
    else:
        return "Get for New Item"


@app.route('/catalog/<int:category_id>/menu/<int:item_id>/JSON')
def showItemJSON(category_id, item_id):
    """Show a catalog item in JSON format."""


@app.route(
    '/catalog/<int:category_id>/menu/<int:item_id>/edit',
    methods=['GET', 'POST']
    )
def editItem(category_id, item_id):
    """Handle the editing of existing catalog items."""
    if request.method == 'POST':
        return "Post for edit item."
    else:
        return "Get for edit item."


@app.route(
    '/catalog/<int:category_id>/item/<int:item_id>/delete',
    methods=['GET', 'POST']
    )
def deleteItem(category_id, item_id):
    """Handle the deletion of catalog items."""
    if request.method == 'POST':
        return "Post for Delete Item"
    else:
        return "Get for Delete Item"


if __name__ == '__main__':
    app.secret_key = "L0NG#hArd$ecret_qi"
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
