from flask import Flask, request, redirect
app = Flask(__name__)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Restaurant, MenuItem

from html_builder import HTML_Builder as HB
import query_db

engine = create_engine('sqlite:///restaurantmenu.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

@app.route('/')
@app.route('/restaurants')
def allRestaurants():
    restaurants = query_db.get_all(session, Restaurant)

    output = HB()
    output.add_html("""
        <h1>Your restaurants</h1>
        """
        )

    for restaurant in restaurants:
        output.add_html("""
            <h4>%s</h4>
            <a href="%s">see menu items</a>
            <hr />
            """ % (restaurant.name, '/restaurants/' + str(restaurant.id))
            )

    return output.get_html()

@app.route('/restaurants/<int:restaurant_id>/')
def restaurantMenu(restaurant_id):
    restaurant = session.query(Restaurant).filter_by(id = restaurant_id).one()
    items = session.query(MenuItem).filter_by(restaurant_id = restaurant_id)

    output = HB()

    output.add_html("""
        <h1>%s</h1>
        """ % restaurant.name
        )

    output.add_html("""
        <a href='%snew-item'>create a new item</a>
        <br />
        <a href='/restaurants'>back to all restaurants</a>
        """ % request.path
        )

    for item in items:
        item_path = request.path + str(item.id) + '/'
        output.add_html("""
            <h4> %s </h4>
            <p> %s </p>
            <p> %s </p>
            <a href=%sedit>edit</a>
            <a href=%sdelete>delete</a>
            <hr />
        """ % (item.name, item.price, item.description, item_path, item_path)
        )

    return output.get_html()


@app.route('/restaurants/<int:restaurant_id>/new-item/', methods=['GET', 'POST'])
def newMenuItem(restaurant_id):
    restaurant = session.query(Restaurant).filter_by(id = restaurant_id).one()
    if request.method == 'GET':
        output = HB()
        output.add_html("""
            <h1> Create a new menu item for %s </h1>
            <form method='POST' action='%s'>
                <label>Name:
                    <input name='name'>
                </label>
                <br />
                <label>Price:
                    <input name='price'>
                </label>
                <br />
                <label>Description:
                    <input name='description'>
                </label>
                <br />
                <label>Course:
                    <input name='course'>
                </label>
                <br />
                <input type='submit' value='CREATE'>
            </form>
            """ % (restaurant.name, request.path)
            )
        return output.get_html()

    if request.method == 'POST':
        params = request.form
        try:
            item = MenuItem(
                    name=params['name'],
                    price=params['price'],
                    course=params['course'],
                    description=params['description'],
                    restaurant=restaurant
                    )
            session.add(item)
            session.commit()

            output = HB()
            output.add_html("""
                <h1>Successfuly create %s </h1>
                <a href="%s">Back to %s</a>
                """ % (params['name'], '/'.join(request.path.split('/')[:3]), restaurant.name)
                )
            return output.get_html()

        except:
            session.rollback()
            raise
            output = HB()
            output.add_html("""
                <h1>Failed to create new menu item</h1>
                <a href=%s> try again </a>
                <a href='/retaurants> back to restaurants </a>
                """ % request.path
                )
            return output.get_html()


@app.route(
    '/restaurants/<int:restaurant_id>/<int:menu_id>/edit',
    methods=['GET','POST']
    )
def editMenuItem(restaurant_id, menu_id):
    restaurant = session.query(Restaurant).filter_by(id = restaurant_id).one()
    menuItem = session.query(MenuItem).filter_by(id = menu_id).one()
    if request.method == 'GET':
        output = HB()
        output.add_html("""
            <h1> Edit %s for %s </h1>
            <form method='POST' action='%s'>
                <label>Name:
                    <input name='name' value='%s'>
                </label>
                <br />
                <label>Price:
                    <input name='price' value='%s'>
                </label>
                <br />
                <label>Description:
                    <input name='description' value='%s'>
                </label>
                <br />
                <label>Course:
                    <input name='course' value='%s'>
                </label>
                <br />
                <input type='submit' value='SUBMIT'>
            </form>
            """ % (menuItem.name, restaurant.name, request.path, menuItem.name, menuItem.price, menuItem.description, menuItem.course))
        return output.get_html()

    if request.method == 'POST':
        params = request.form
        try:
            if menuItem.name != params['name']:
                menuItem.name = params['name']
            if menuItem.price != params['price']:
                menuItem.price = params['price']
            if menuItem.description != params['description']:
                menuItem.description = params['description']
            if menuItem.course != params['course']:
                menuItem.course = params['course']

            session.add(menuItem)
            session.commit()

            output = HB()
            output.add_html("""
                <h1>Successfuly edited %s </h1>
                <a href="%s">Back to %s</a>
                """ % (params['name'], ('/').join(request.path.split('/')[:3])
                    + '/', restaurant.name)
                )
            return output.get_html()

        except:
            session.rollback()
            raise
            output = HB()
            output.add_html("""
                <h1>Failed to create new menu item</h1>
                <a href=%s> try again </a>
                <a href='/retaurants> back to restaurants </a>
                """ % request.path
                )
            return output.get_html()


@app.route('/restaurants/<int:restaurant_id>/<int:menu_id>/delete/',
    methods=['GET', 'POST'])
def deleteMenuItem(restaurant_id, menu_id):
    menuItem = query_db.get_one(session, MenuItem, menu_id)
    restaurant = query_db.get_one(session, Restaurant, restaurant_id)
    output = HB()

    if request.method == 'GET':
        output.add_html("""
            <h1>Are you sure you want to delete %s</h1>
            <form method='POST' action='%s'>
                <input type='submit' name='should_delete' value='YES'>
                <input type='submit' name='should_delete' value='NO'>
            </form>
            """ % (menuItem.name, request.path)
            )
        return output.get_html()

    if request.method == 'POST':
        restaurant_path = '/'.join(request.path.split('/')[:3])
        if request.form['should_delete'].lower() == 'yes':
            try:
                query_db.delete(session, menuItem)
                session.commit()

                output.add_html("""
                    <h1>Successfully deleted %s</h1>
                    <a href='%s'>Back to %s</a>
                    """ % (menuItem.name, restaurant_path, restaurant.name)
                    )
                return output.get_html()
            except:
                session.rollback()
                raise
                output.add_html("""
                    <h1>Failed to create new menu item</h1>
                    <a href=%s> try again </a>
                    <a href='/retaurants> back to restaurants </a>
                    """ % request.path
                    )
                return output.get_html()
        else:
            return redirect('/restaurants/%s/' % restaurant.id)

if __name__ == '__main__':
    app.debug = True
    app.run(host = '0.0.0.0', port=5000)
