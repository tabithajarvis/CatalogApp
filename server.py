"""
Catalog Server.

This module runs the server for the Catalog web app.  The Catalog web app is
used to manage a catalog of items.
"""

from flask import \
    Flask, request, render_template, jsonify  # , redirect, url_for, flash

from cdb_setup import User, Category, Item

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Create app
app = Flask(__name__)

# Create DB session
engine = create_engine('sqlite:///catalog.db')
DBSession = sessionmaker(bind=engine)
session = DBSession()


# DB Query Helper Functions
def getCategory(id):
    """Get a category object by id."""
    return session.query(Category).filter(Category.id == id).first()


def getCategoryItems(id):
    """Get a list of items by category id."""
    return session.query(Item).filter(Item.category_id == id).all()


def getItem(id):
    """Get an item by id."""
    return session.query(Item).filter(Item.id == id).first()


def getUser(id):
    """Get a user by id."""
    return session.query(User).filter(User.id == id).first()


# Authorization routing
@app.route('/login')
def showLogin():
    """Show the login page."""
    return render_template("login.html")


# App routing
@app.route('/')
@app.route('/catalog')
def showCatalog():
    """Show the front page of the catalog app."""
    categories = session.query(Category).all()
    return render_template("catalog.html", categories=categories)


@app.route('/catalog/JSON')
def showCatalogJSON():
    """Show the Catalog in JSON."""
    categories = session.query(Category).all()
    return jsonify(categories=[c.serialize for c in categories])


@app.route('/catalog/new', methods=['GET', 'POST'])
def newCategory():
    """Handle the addition of new categories."""
    if request.method == 'POST':
        return "Post for New Category"
    else:
        return render_template("new_category.html")


@app.route('/catalog/<int:category_id>/edit', methods=['GET', 'POST'])
def editCategory(category_id):
    """Handle the editing of existing categories."""
    if request.method == 'POST':
        return "Post for Edit Category"
    else:
        category = getCategory(category_id)
        return render_template("edit_category.html", category=category)


@app.route('/catalog/<int:category_id>/delete', methods=['GET', 'POST'])
def deleteCategory(category_id):
    """Handle the deletion of categories."""
    if request.method == 'POST':
        return "Post for Delete Category"
    else:
        category = getCategory(category_id)
        return render_template("delete_category.html", category=category)


@app.route('/catalog/<int:category_id>')
@app.route('/catalog/<int:category_id>/items')
def showCategory(category_id):
    """Show all items in a category."""
    items = getCategoryItems(category_id)
    render_template("category.html", items=items)


@app.route('/catalog/<int:category_id>/items/JSON')
def showCategoryJSON(category_id):
    """Show all items in a category in JSON format."""
    items = getCategoryItems(category_id)
    return jsonify(Items=[i.serialize for i in items])


@app.route('/catalog/<int:category_id>/items/new', methods=['GET', 'POST'])
def newItem(category_id):
    """Handle the addition of new catalog items."""
    if request.method == 'POST':
        return "Post for New Item"
    else:
        category = getCategory(category_id)
        return render_template("new_item.html", category=category)


@app.route('/catalog/<int:category_id>/items/<int:item_id>')
def showItem(category_id, item_id):
    """Show a catalog item."""
    item = getItem(item_id)
    return render_template("item.html", item=item)


@app.route('/catalog/<int:category_id>/items/<int:item_id>/JSON')
def showItemJSON(category_id, item_id):
    """Show a catalog item in JSON format."""
    item = getItem(item_id)
    return jsonify(Item=item.serialize)


@app.route(
    '/catalog/<int:category_id>/items/<int:item_id>/edit',
    methods=['GET', 'POST']
    )
def editItem(category_id, item_id):
    """Handle the editing of existing catalog items."""
    if request.method == 'POST':
        return "Post for edit item."
    else:
        item = getItem(item_id)
        return render_template("edit_item.html", item=item)


@app.route(
    '/catalog/<int:category_id>/items/<int:item_id>/delete',
    methods=['GET', 'POST']
    )
def deleteItem(category_id, item_id):
    """Handle the deletion of catalog items."""
    if request.method == 'POST':
        return "Post for Delete Item"
    else:
        # TODO: Add check here for if category would be empty after delete.
        #  If so, delete category.
        item = getItem(item_id)
        return render_template("delete_item.html", item=item)


if __name__ == '__main__':
    app.secret_key = "L0NG#hArd$ecret_qi"
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
