"""
Catalog Server.

This module runs the server for the Catalog web app.  The Catalog web app is
used to manage a catalog of items.
"""

from flask import \
    Flask, request, render_template, jsonify, redirect, flash, url_for, \
    make_response
from flask import session as login_session
from functools import wraps

from cdb_setup import Base, User, Category, Item

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from oauth2client import client

import json
import random
import string
import httplib2
import requests

# Create app
app = Flask(__name__)

# Create DB session
engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

# Create client id for oauth
CLIENT_ID = json.loads(
    open('client_secret.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Catalog App"


# DB Query Helper Functions
def getCategory(id):
    """Get a category object by id."""
    return session.query(Category).filter_by(id=id).first()


def getCategoryItems(id):
    """Get a list of items by category id."""
    return session.query(Item).filter_by(category_id=id).all()


def getItem(id):
    """Get an item by id."""
    return session.query(Item).filter_by(id=id).first()


def getUser(**kw):
    """Get a user by ID."""
    user = session.query(User)

    if not user:
        return

    if kw.get('user_id'):
        user = user.filter_by(id=kw['user_id'])
    elif kw.get('email'):
        user = user.filter_by(email=kw['email'])
    if user:
        return user.first()


def getCurrentUser():
    """Get the current user."""
    return session.query(User).filter_by(email=login_session.get('email')).first()


# JSON helper functions
def JSONresponse(message, code):
    """Formulate a JSON response with the given message and code."""
    response = make_response(json.dumps(message), code)
    response.headers['Content-type'] = 'application/json'
    return response


# User helper functions
def createUser(login_session):
    """Create new user from a login_session."""
    newUser = User(
        name=login_session['username'],
        email=login_session['email'],
        picture=login_session['picture']
        )
    session.add(newUser)
    session.commit()

    # Return the user
    return session.query(User).filter_by(email=login_session['email']).one()


# Permissions-checking functions
def login_required(f):
    """Wrap functions that require login with login check."""
    @wraps(f)
    def wrapper(**kw):
        user = getCurrentUser()
        if user:
            return f(**kw)
        else:
            flash("You must be logged in to perform this action.")
            return redirect(url_for('showLogin'))
    return wrapper


def category_exists(f):
    """Wrap functions that occur on a category id to verify existance."""
    @wraps(f)
    def wrapper(**kw):
        category = getCategory(kw['category_id'])
        if category:
            return f(**kw)
        else:
            flash("The category in the URL does not exist.")
            return redirect(url_for('showCatalog'))
    return wrapper


def item_exists(f):
    """Wrap functions that occur on a category id to verify existance."""
    @wraps(f)
    def wrapper(**kw):
        category = getCategory(kw['category_id'])
        if not category:
            flash("The category in the URL does not exist.")
            return redirect(url_for('showCatalog'))

        item = getItem(kw['item_id'])
        if not item:
            flash("The item in the URL does not exist.")
            return redirect(url_for('showCategory', kw['category_id']))

        return f(**kw)
    return wrapper


def owns_category(f):
    """Wrap functions on category pages intended to be used by owners."""
    @wraps(f)
    def wrapper(**kw):
        category = getCategory(kw['category_id'])
        user = getCurrentUser()

        if not category:
            flash("The category in the URL does not exist.")
            return redirect(url_for('showCatalog'))
        elif not user:
            flash("You must be logged in to perform this action.")
            return redirect(url_for('showLogin'))
        elif not user.id == category.user_id:
            flash("You cannot edit categories created by others.")
            return redirect(url_for('showCategory', category_id=category.id))
        else:
            return f(**kw)
    return wrapper


def owns_item(f):
    """Wrap functions on item actions intended to be used by owners."""
    @wraps(f)
    def wrapper(**kw):
        category = getCategory(kw['category_id'])
        if not category:
            flash("The category specified in the URL does not exist.")
            return redirect(url_for('showCatalog'))

        item = getItem(kw['item_id'])
        if not item:
            flash("The item specified in the URL does not exist.")
            return redirect(url_for('showCategory', category_id=kw['category_id']))

        user = getCurrentUser()

        if not user:
            flash("You must be logged in to perform this action.")
            redirect(url_for('showLogin'))
        elif not user.id == item.user_id:
            flash("You cannot edit items created by other users")
            redirect(url_for('showItem'), category_id=kw['category_id'], item_id=kw['item_id'])
        else:
            return f(**kw)
    return wrapper


# Authorization routing
@app.route('/login')
def showLogin():
    """Show login."""
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)


# Log out based on provider
@app.route('/logout')
def disconnect():
    """Log out current user."""
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()
            del login_session['gplus_id']
            del login_session['credentials']
        if login_session['provider'] == 'facebook':
            fbdisconnect()
            del login_session['facebook_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        del login_session['provider']
        flash("You have successfully been logged out.")
        return redirect(url_for('showCatalog'))
    else:
        return redirect(url_for('showCatalog'))
        flash("You were not logged in")


@app.route('/gconnect', methods=['POST'])
def gconnect():
    """Log in with google."""
    if request.args.get('state') != login_session['state']:
        return JSONresponse('Invalid state token', 401)
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        flow = client.flow_from_clientsecrets('client_secret.json', scope='')
        flow.redirect_uri = 'postmessage'
        credentials = flow.step2_exchange(code)
    except client.FlowExchangeError:
        print "FlowExchangeError exception."
        return JSONresponse('Failed to upgrade the authorization code', 401)

    # Check that the access token is valid
    access_token = credentials.access_token
    url = (
        'https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
        % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])

    # If there was an error in access token info, abort
    if result.get('error') is not None:
        return JSONresponse(result.get('error'), 50)

    # Verify that the access token is used for the intended user
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        return JSONresponse("Token's user ID doesn't match given user ID", 401)

    # Verify that the access token is valid for this app
    if result['issued_to'] != CLIENT_ID:
        return JSONresponse("Token's client ID does not match app's", 401)

    # Check to see if user is already logged in
    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        return JSONresponse("Current user is already connected", 200)

    # Store the access token in the session for later use
    login_session['credentials'] = credentials
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)
    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    # ADD PROVIDER TO LOGIN SESSION
    login_session['provider'] = 'google'

    # see if user exists, if it doesn't make a new one
    user = getUser(email=data["email"])
    if not user:
        user = createUser(login_session)
    login_session['user_id'] = user.id

    flash("You are now logged in as  %s" % login_session['username'])
    return render_template("login_redirect.html", login_session=login_session)


@app.route('/gdisconnect')
def gdisconnect():
    """Disconnect User."""
    # Only disconnect a connected user.
    credentials = login_session.get('credentials')
    if credentials is None:
        return JSONresponse("Current user is not connected", 401)

    access_token = credentials.access_token
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] != '200':
        # For whatever reason, the given token was invalid.
        return JSONresponse("Failed to revoke token for given user", 400)


# App routing
@app.route('/')
@app.route('/oauth2callback')
@app.route('/catalog')
def showCatalog():
    """Show the front page of the catalog app."""
    categories = session.query(Category).all()
    items = dict()
    for category in categories:
        items[category.name] = getCategoryItems(category.id)
    return render_template("catalog.html", categories=categories, user=getCurrentUser(), items=items)


@app.route('/catalog/JSON')
def showCatalogJSON():
    """Show the Catalog in JSON."""
    categories = session.query(Category).all()
    return jsonify(categories=[c.serialize for c in categories])


@app.route('/catalog/new', methods=['GET'])
@login_required
def newCategory():
    """Show the new category addition page."""
    return render_template("new_category.html")


@app.route('/catalog/new', methods=['POST'])
@login_required
def newCategoryPost():
    """Handle the addition of new categories."""
    user = getCurrentUser()
    category = Category(name=request.form['name'], user=user)
    session.add(category)
    session.commit()
    flash("%s Created" % category.name)
    return redirect(url_for('showCatalog'))


@app.route('/catalog/<int:category_id>/edit', methods=['GET'])
@owns_category
def editCategory(category_id):
    """Show the edit category page."""
    category = getCategory(category_id)
    return render_template("edit_category.html", category=category)


@app.route('/catalog/<int:category_id>/edit', methods=['POST'])
@owns_category
def editCategoryPost(category_id):
    """Handle the editing of existing categories."""
    category = getCategory(category_id)
    category.name = request.form['name']
    session.add(category)
    session.commit()
    flash("%s Updated" % category.name)
    return redirect(url_for('showCatalog'))


@app.route('/catalog/<int:category_id>/delete', methods=['GET'])
@owns_category
def deleteCategory(category_id):
    """Show the delete category page."""
    category = getCategory(category_id)
    return render_template("delete_category.html", category=category)


@app.route('/catalog/<int:category_id>/delete', methods=['POST'])
@owns_category
def deleteCategoryPost(category_id):
    """Handle the deletion of categories."""
    category = getCategory(category_id)
    session.delete(category)
    session.commit()
    flash("%s Deleted" % category.name)
    return redirect(url_for('showCatalog'))


@app.route('/catalog/<int:category_id>')
@app.route('/catalog/<int:category_id>/items')
@category_exists
def showCategory(category_id):
    """Show all items in a category."""
    category = getCategory(category_id)
    items = getCategoryItems(category_id)
    return render_template("category.html", category=category, items=items)


@app.route('/catalog/<int:category_id>/items/JSON')
@category_exists
def showCategoryJSON(category_id):
    """Show all items in a category in JSON format."""
    items = getCategoryItems(category_id)
    return jsonify(Items=[i.serialize for i in items])


@app.route('/catalog/<int:category_id>/items/new', methods=['GET'])
@category_exists
@login_required
def newItem(category_id):
    """Show the add new item page."""
    category = getCategory(category_id)
    return render_template("new_item.html", category=category)


@app.route('/catalog/<int:category_id>/items/new', methods=['POST'])
@category_exists
@login_required
def newItemPost(category_id):
    """Handle the addition of new catalog items."""
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
    return redirect(
        url_for('showItem', category_id=category_id, item_id=item.id))


@app.route('/catalog/<int:category_id>/items/<int:item_id>')
@item_exists
def showItem(category_id, item_id):
    """Show a catalog item."""
    item = getItem(item_id)
    return render_template("item.html", item=item, category=item.category)


@app.route('/catalog/<int:category_id>/items/<int:item_id>/JSON')
@item_exists
def showItemJSON(category_id, item_id):
    """Show a catalog item in JSON format."""
    item = getItem(item_id)
    return jsonify(Item=item.serialize)


@app.route('/catalog/<int:category_id>/items/<int:item_id>/edit',
           methods=['GET'])
@owns_item
def editItem(category_id, item_id):
    """Show the edit item page."""
    item = getItem(item_id)
    return render_template("edit_item.html", item=item)


@app.route('/catalog/<int:category_id>/items/<int:item_id>/edit',
           methods=['POST'])
@owns_item
def editItemPost(category_id, item_id):
    """Handle the editing of existing catalog items."""
    item = getItem(item_id)
    item.name = request.form['name']
    item.description = request.form['description']
    item.picture = request.form['picture']
    session.add(item)
    session.commit()
    flash("%s Updated" % item.name)
    return redirect(
        url_for('showItem', category_id=category_id, item_id=item_id)
        )


@app.route('/catalog/<int:category_id>/items/<int:item_id>/delete',
           methods=['GET'])
@owns_item
def deleteItem(category_id, item_id):
    """Show the delete item page."""
    # TODO: Add check here for if category would be empty after delete.
    #  If so, delete category.
    item = getItem(item_id)
    return render_template("delete_item.html", item=item)


@app.route('/catalog/<int:category_id>/items/<int:item_id>/delete',
           methods=['POST'])
@owns_item
def deleteItem(category_id, item_id):
    """Handle the deletion of catalog items."""
    item = getItem(item_id)
    category = getCategory(category_id)
    session.delete(item)
    session.commit()
    flash("%s Deleted." % item.name)
    return redirect(url_for("showCategory", category=category))


if __name__ == '__main__':
    app.secret_key = "L0NG#hArd$ecret_qi"
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
