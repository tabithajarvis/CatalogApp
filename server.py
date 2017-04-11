"""
Catalog Server.

This module runs the server for the Catalog web app.  The Catalog web app is
used to manage a catalog of items.
"""

from flask import \
    Flask, request, render_template, jsonify, redirect, flash, url_for

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


def getCurrentUser():
    """Get the current user."""
    # TODO: fix.  This currently only returns the first user
    # return getUser(GET_USER_ID_FROM_COOKIE)
    return session.query(User).first()


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
        category = Category(name=request.form['name'])
        session.add(category)
        session.commit()
        flash("%s Created" % category.name)
        return redirect(url_for('showCatalog'))
    else:
        return render_template("new_category.html")


@app.route('/catalog/<int:category_id>/edit', methods=['GET', 'POST'])
def editCategory(category_id):
    """Handle the editing of existing categories."""
    if request.method == 'POST':
        category = getCategory(category_id)
        category.name = request.form['name']
        session.add(category)
        session.commit()
        flash("%s Updated" % category.name)
        return redirect(url_for('showCatalog'))
    else:
        category = getCategory(category_id)
        return render_template("edit_category.html", category=category)


@app.route('/catalog/<int:category_id>/delete', methods=['GET', 'POST'])
def deleteCategory(category_id):
    """Handle the deletion of categories."""
    if request.method == 'POST':
        category = getCategory(category_id)
        session.delete(category)
        session.commit()
        flash("%s Deleted" % category.name)
        return redirect(url_for('showCatalog'))
    else:
        category = getCategory(category_id)
        return render_template("delete_category.html", category=category)


@app.route('/catalog/<int:category_id>')
@app.route('/catalog/<int:category_id>/items')
def showCategory(category_id):
    """Show all items in a category."""
    category = getCategory(category_id)
    items = getCategoryItems(category_id)
    return render_template("category.html", category=category, items=items)


@app.route('/catalog/<int:category_id>/items/JSON')
def showCategoryJSON(category_id):
    """Show all items in a category in JSON format."""
    items = getCategoryItems(category_id)
    return jsonify(Items=[i.serialize for i in items])


@app.route('/catalog/<int:category_id>/items/new', methods=['GET', 'POST'])
def newItem(category_id):
    """Handle the addition of new catalog items."""
    if request.method == 'POST':
        item = Item(
            name=request.form['name'],
            description=request.form['description'],
            picture=request.form['picture'],
            category=getCategory(category_id),
            user=getCurrentUser()
            )
        session.add(item)
        session.commit()
        flash("%s Created" % item.name)
        return redirect(url_for('showItem', category_id=category_id, item_id=item.id))
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
        item = getItem(item_id)
        item.name = request.form['name']
        item.description = request.form['description']
        item.picture = request.form['picture']
        session.add(item)
        session.commit()
        flash("%s Updated" % item.name)
        return redirect(url_for('showItem', item=item))
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
        item = getItem(item_id)
        category = getCategory(category_id)
        session.delete(item)
        session.commit()
        flash("%s Deleted." % item.name)
        return redirect(url_for("showCategory", category=category))
    else:
        # TODO: Add check here for if category would be empty after delete.
        #  If so, delete category.
        item = getItem(item_id)
        return render_template("delete_item.html", item=item)


if __name__ == '__main__':
    app.secret_key = "L0NG#hArd$ecret_qi"
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
