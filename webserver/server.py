#!/usr/bin/env python2.7

"""
Columbia W4111 Intro to databases
Example webserver

To run locally

    python server.py

Go to http://localhost:8111 in your browser


A debugger such as "pdb" may be helpful for debugging.
Read about it online.
"""

import os
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask
from flask import Flask, request, render_template, g, redirect, Response, flash, session, abort, url_for
from datetime import datetime
import time
import random
import hashlib
import credentials

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)


# XXX: The Database URI should be in the format of: 
#
#     postgresql://USER:PASSWORD@<IP_OF_POSTGRE_SQL_SERVER>/<DB_NAME>
#
# For example, if you had username ewu2493, password foobar, then the following line would be:
#
#     DATABASEURI = "postgresql://ewu2493:foobar@<IP_OF_POSTGRE_SQL_SERVER>/postgres"
#
# For your convenience, we already set it to the class database

# Use the DB credentials you received by e-mail
DB_USER = credentials.get_db_user()
DB_PASSWORD = credentials.get_db_password()

DB_SERVER = "w4111.cisxo09blonu.us-east-1.rds.amazonaws.com"

DATABASEURI = "postgresql://"+DB_USER+":"+DB_PASSWORD+"@"+DB_SERVER+"/w4111"


#
# This line creates a database engine that knows how to connect to the URI above
#
engine = create_engine(DATABASEURI)


# Here we create a test table and insert some values in it
engine.execute("""DROP TABLE IF EXISTS test;""")
engine.execute("""CREATE TABLE IF NOT EXISTS test (
  id serial,
  name text
);""")
engine.execute("""INSERT INTO test(name) VALUES ('grace hopper'), ('alan turing'), ('ada lovelace');""")


@app.before_request
def before_request():
  """
  This function is run at the beginning of every web request 
  (every time you enter an address in the web browser).
  We use it to setup a database connection that can be used throughout the request

  The variable g is globally accessible
  """
  try:
    g.conn = engine.connect()
  except:
    print("uh oh, problem connecting to database")
    import traceback; traceback.print_exc()
    g.conn = None

    
@app.teardown_request
def teardown_request(exception):
  """
  At the end of the web request, this makes sure to close the database connection.
  If you don't the database could run out of memory!
  """
  try:
    g.conn.close()
  except Exception as e:
    pass


#
# @app.route is a decorator around index() that means:
#   run index() whenever the user tries to access the "/" path using a GET request
#
# If you wanted the user to go to e.g., localhost:8111/foobar/ with POST or GET then you could use
#
#       @app.route("/foobar/", methods=["POST", "GET"])
#
# PROTIP: (the trailing / in the path is important)
# 
# see for routing: http://flask.pocoo.org/docs/0.10/quickstart/#routing
# see for decorators: http://simeonfranklin.com/blog/2012/jul/1/python-decorators-in-12-steps/
#
@app.route('/')
def index():
  """
  request is a special object that Flask provides to access web request information:

  request.method:   "GET" or "POST"
  request.form:     if the browser submitted a form, this contains the data in the form
  request.args:     dictionary of URL arguments e.g., {a:1, b:2} for http://localhost?a=1&b=2

  See its API: http://flask.pocoo.org/docs/0.10/api/#incoming-request-data
  """

  # DEBUG: this is debugging code to see what request looks like
  print(request.args)

  # Login logic
  if not session.get('logged_in'):
    return render_template('login.html')
  else:

    # Query for restaurants
    cursor = g.conn.execute("""SELECT location_id, location_name, location_address, location_city
        FROM restaurant""")
    restaurants = []
    for result in cursor:
      restaurants.append(dict(location_id=result['location_id'],
                              location_name=result['location_name'],
                              location_address=result['location_address'],
                              location_city=result['location_city']))
    cursor.close()

    # Query for employeeof
    employeeof_location_id = None
    cmd = "SELECT location_id FROM employeeof WHERE user_id = :user_id";
    cursor = g.conn.execute(text(cmd), user_id = session['user_id']);
    for result in cursor:
      employeeof_location_id = result['location_id']
    cursor.close()
    
    #
    # Flask uses Jinja templates, which is an extension to HTML where you can
    # pass data to a template and dynamically generate HTML based on the data
    # (you can think of it as simple PHP)
    # documentation: https://realpython.com/blog/python/primer-on-jinja-templating/
    #
    context = dict(data = restaurants, employeeof_location_id = employeeof_location_id, user_id=session.get('user_id'))

    #
    # render_template looks in the templates/ folder for files.
    # for example, the below file reads template/index.html
    #
    return render_template("index.html", **context)


# Display menus of selected restaurant
@app.route('/<string:location_id>/menu', methods=['GET', 'POST'])
def menu(location_id):
  # Login logic
  if not session.get('logged_in'):
    return render_template('login.html')
  else:

    # Query for menus
    cmd = "SELECT menu_id, menu_name FROM menu WHERE location_id = :location_id";
    cursor = g.conn.execute(text(cmd), location_id = location_id);
    
    menus = []
    for result in cursor:
      menus.append(dict(menu_id=result['menu_id'],
                        menu_name=result['menu_name']))
    cursor.close()

    # Query for location_name
    cmd = "SELECT location_name FROM restaurant WHERE location_id = :location_id";
    cursor = g.conn.execute(text(cmd), location_id = location_id);
    
    for result in cursor:
      location_name = result['location_name']
    cursor.close()

    context = dict(data = menus, location_name = location_name)

    return render_template("menu.html", **context)


# Display items of selected restaurant and menu
@app.route('/<string:menu_id>/items', methods=['GET', 'POST'])
def items(menu_id):
  # Login logic
  if not session.get('logged_in'):
    return render_template('login.html')
  else:

    # Query for items
    cmd = """SELECT menu_id, item_id, menu_section_name, menu_item_name, menu_item_description, attribute_name, menu_item_price
        FROM item WHERE menu_id = :menu_id""";
    cursor = g.conn.execute(text(cmd), menu_id = menu_id);
    
    items = []
    for result in cursor:
      items.append(dict(item_id=result['item_id'],
                        menu_section_name=result['menu_section_name'],
                        menu_item_name=result['menu_item_name'],
                        menu_item_description=result['menu_item_description'],
                        attribute_name=result['attribute_name'],
                        menu_item_price=round(result['menu_item_price'], 2)))
    cursor.close()
    
    # Query for location_id
    cmd = "SELECT location_id, menu_name FROM menu WHERE menu_id = :menu_id";
    cursor = g.conn.execute(text(cmd), menu_id = menu_id);
    
    for result in cursor:
      location_id = result['location_id']
      menu_name = result['menu_name']
    cursor.close()

    # Query for location_name
    cmd = "SELECT location_name FROM restaurant WHERE location_id = :location_id";
    cursor = g.conn.execute(text(cmd), location_id = location_id);
    
    for result in cursor:
      location_name = result['location_name']
    cursor.close()

    context = dict(data = items, location_id = location_id,
                   location_name = location_name, menu_name = menu_name)

    if request.method == 'GET':
      return render_template("items.html", **context)
    
    if request.method == 'POST':
      # Generate order_id
      machine_id = '12345678'
      secs = str(int(round(time.time())))
      counter = str(random.randint(0, 9999999))
      order_id = secs + machine_id + counter

      # Generate order timestamp
      dt = datetime.now()

      # Retrieve pickup information
      pickup_check = request.form.getlist('pickup')
      if len(pickup_check) > 0:
        pickup = 'true'
      else:
        pickup = 'false'

      # Initialize confirmation message
      conf_msg = ''

      n_ordered = 0
      for item_id, quantity in request.form.items():
        if quantity != '0' and quantity != 'pickup':
          n_ordered += 1
          # Retrieve menu_item_name and menu_name
          cmd = "SELECT menu_item_name, menu_section_name FROM item WHERE item_id = :item_id";
          cursor = g.conn.execute(text(cmd), item_id = item_id);
          for result in cursor:
            menu_item_name = result['menu_item_name']
            menu_name = result['menu_section_name']
          cursor.close()

          # Insert into ordered
          cmd = """INSERT INTO ordered(order_id, order_item_id, order_placed, quantity, pickup, menu_item_name, menu_name, location_id)
              VALUES (:order_id, :item_id, :dt, :quantity, :pickup, :menu_item_name, :menu_name, :location_id)""";
          g.conn.execute(text(cmd), order_id=order_id, item_id=item_id, dt=dt, quantity=quantity,
                         pickup=pickup, menu_item_name=menu_item_name, menu_name=menu_name,
                         location_id=location_id);
          
          # For first item insert into placed
          if n_ordered == 1:
            cmd = """INSERT INTO placed(customer_id, order_id, order_item_id, date_placed)
                VALUES (:customer_id, :order_id, :item_id, :dt)""";
            g.conn.execute(text(cmd), customer_id=session['user_id'], order_id=order_id,
                           item_id=item_id, dt=dt);
          
          # Append confirmation message
          conf_msg += menu_item_name + ' x ' + quantity + '\n'

      # Show order confirmation
      if len(conf_msg) > 0:
        flash(conf_msg)
      return render_template("items.html", **context)


# Employee console landing page
@app.route('/employee', methods=['GET'])
def employee():
  if not session.get('logged_in'):
    return render_template('login.html')
  else:
    # Get locations of employee
    cmd = "SELECT location_id FROM employeeof WHERE user_id = :user_id";
    cursor = g.conn.execute(text(cmd), user_id=session['user_id']);
  
    employee_location_ids = []
    for result in cursor:
      employee_location_ids.append(result['location_id'])
    cursor.close()

    location_info = []
    for location_id in employee_location_ids:
      # Query for location_name
      cmd = "SELECT location_name FROM restaurant WHERE location_id = :location_id";
      cursor = g.conn.execute(text(cmd), location_id = location_id);
    
      for result in cursor:
        location_info.append(str(location_id) + ' ' + result['location_name'])
      cursor.close()
  
    context = dict(employee_location_ids=employee_location_ids, location_info=location_info)

    return render_template("employee.html", **context)


@app.route('/<string:location_id>/additem', methods=['GET', 'POST'])
def additem(location_id):
  if not session.get('logged_in'):
    return render_template('login.html')
  else:
    # Query for location_name
    cmd = "SELECT location_name FROM restaurant WHERE location_id = :location_id";
    cursor = g.conn.execute(text(cmd), location_id = location_id);

    for result in cursor:
      location_name = result['location_name']
    cursor.close()

    # Get menus for the location
    menu_info = []
    cmd = "SELECT menu_id, menu_name FROM menu WHERE location_id = :location_id";
    cursor = g.conn.execute(text(cmd), location_id=location_id);
    for result in cursor:
      menu_info.append({'menu_id': result['menu_id'], 'menu_name': result['menu_name']})
    cursor.close()
  
    context = dict(location_id=location_id, location_name=location_name, menu_info=menu_info)

    if request.method == 'GET':
      return render_template('additem.html', **context)

    if request.method == 'POST':
      menu_id = request.form['menus']
      item_name = request.form['add-item-name']
      menu_section_name = request.form['add-item-section']
      item_description = request.form['add-item-description']
      item_attributes = request.form['add-item-attributes']
      item_price = request.form['add-item-price']
      print(menu_id, item_name, item_description, item_attributes, item_price)

      # Check item name
      if len(item_name) < 1:
        flash('Enter an item name')
        return render_template('additem.html', **context)

      if len(item_price) < 1:
        flash('Enter an item price')
        return render_template('additem.html', **context)

      # Generate new item id
      for menu in context['menu_info']:
        if menu['menu_id'] == str(menu_id):
          menu_name = menu['menu_name']
      temp_string = str(location_id) + menu_name + item_name
      item_id = hashlib.md5(temp_string.encode('utf-8')).hexdigest()
      
      # Insert new item
      cmd = """INSERT INTO item(menu_id, item_id, menu_section_name, menu_item_name, menu_item_description, attribute_name, menu_item_price)
          VALUES (:menu_id, :item_id, :menu_section_name, :item_name, :item_description, :item_attributes, :item_price)"""
      g.conn.execute(text(cmd), menu_id=menu_id, item_id=item_id, menu_section_name=menu_section_name,
                     item_name=item_name, item_description=item_description,
                     item_attributes=item_attributes, item_price=item_price)
      
      flash('New item: ' + item_name)
      return render_template('additem.html', **context)


@app.route('/<string:location_id>/updateitem', methods=['GET', 'POST'])
def updatedeleteitem(location_id):
  if not session.get('logged_in'):
    return render_template('login.html')
  else:
    # Query for location_name
    cmd = "SELECT location_name FROM restaurant WHERE location_id = :location_id";
    cursor = g.conn.execute(text(cmd), location_id = location_id);

    for result in cursor:
      location_name = result['location_name']
    cursor.close()

    # Get menus for the location
    menu_info = []
    cmd = "SELECT menu_id, menu_name FROM menu WHERE location_id = :location_id";
    cursor = g.conn.execute(text(cmd), location_id=location_id);
    for result in cursor:
      menu_info.append({'menu_id': result['menu_id'], 'menu_name': result['menu_name']})
    cursor.close()

    # Get items for all menus
    item_info = []
    for menu in menu_info:
      cmd = """SELECT item_id, menu_section_name, menu_item_name, menu_item_description, attribute_name, menu_item_price
          FROM item WHERE menu_id = :menu_id"""
      cursor = g.conn.execute(text(cmd), menu_id=menu['menu_id'])
      for result in cursor:
        item_info.append({'menu_name': menu['menu_name'], 'item_id': result['item_id'],
                          'menu_item_name': result['menu_item_name'],
                          'menu_section_name': result['menu_section_name'],
                          'menu_item_description': result['menu_item_description'],
                          'attribute_name': result['attribute_name'],
                          'menu_item_price': round(result['menu_item_price'], 2)})
      cursor.close()
      
    context = dict(location_id=location_id, location_name=location_name, item_info=item_info)

    if request.method == 'GET':
      return render_template('updateitem.html', **context)

    if request.method == 'POST':
      update_boxes = request.form.getlist('update-box')
      menu_sections = request.form.getlist('menu-section')
      item_names = request.form.getlist('menu-item-name')
      item_descriptions = request.form.getlist('menu-item-description')
      attribute_names = request.form.getlist('menu-attribute-name')
      item_prices = request.form.getlist('update-item-price')

      # Find items selected for update
      update_items = [int(x.split('-')[0]) for x in update_boxes]

      # Check that updated items have updated content
      for item_idx in update_items:
        if len(menu_sections[item_idx]) == 0 and len(item_names[item_idx]) == 0 and len(item_descriptions[item_idx]) == 0 and len(attribute_names[item_idx]) == 0 and len(item_prices[item_idx]) == 0:
          flash('Warning: Please enter some item information for updated items')
          render_template('updateitem.html', **context)

      n_updated = 0
      # Update items and context
      for i, item_idx in enumerate(update_items):
        item_id = update_boxes[i].split('-')[2]
        updated_item = item_info[i]
        if len(menu_sections[item_idx]) > 0:
          cmd = 'UPDATE item SET menu_section_name = :menu_section WHERE item_id = :item_id';
          g.conn.execute(text(cmd), menu_section=menu_sections[item_idx], item_id=item_id);
          updated_item['menu_section_name'] = menu_sections[item_idx]
        if len(item_names[item_idx]) > 0:
          cmd = 'UPDATE item SET menu_item_name = :item_name WHERE item_id = :item_id';
          g.conn.execute(text(cmd), item_name=item_names[item_idx], item_id=item_id);
          updated_item['menu_item_name'] = item_names[item_idx]
        if len(item_descriptions[item_idx]) > 0:
          cmd = 'UPDATE item SET menu_item_description = :item_description WHERE item_id = :item_id';
          g.conn.execute(text(cmd), item_description=item_descriptions[item_idx], item_id=item_id);
          updated_item['menu_item_description'] = item_descriptions[item_idx]
        if len(attribute_names[item_idx]) > 0:
          cmd = 'UPDATE item SET attribute_name = :attribute_name WHERE item_id = :item_id';
          g.conn.execute(text(cmd), attribute_name=attribute_names[item_idx], item_id=item_id);
          updated_item['attribute_name'] = attribute_names[item_idx]
        if len(item_prices[item_idx]) > 0:
          cmd = 'UPDATE item SET menu_item_price = :item_price WHERE item_id = :item_id';
          g.conn.execute(text(cmd), item_price=item_prices[item_idx], item_id=item_id);
          updated_item['menu_item_price'] = item_prices[item_idx]

        item_info[i] = updated_item
        n_updated += 1

        
      context = dict(location_id=location_id, location_name=location_name, item_info=item_info)
        
      flash('Number Updated: ' + str(n_updated))
      return render_template('updateitem.html', **context)

  
# Example alternate route
@app.route('/another')
def another():
  return render_template("anotherfile.html")


# Example of adding new data to the database
@app.route('/add', methods=['POST'])
def add():
  name = request.form['name']
  print(name)
  cmd = 'INSERT INTO test(name) VALUES (:name1)';
  g.conn.execute(text(cmd), name1 = name);
  return redirect('/')


# Add new user and customer to database
@app.route('/register', methods=['GET', 'POST'])
def register():
  # Query for location information for employee dropdown
  cmd = 'SELECT * FROM restaurant';
  cursor = g.conn.execute(text(cmd));
  restaurants = []
  for result in cursor:
    restaurants.append(dict(location=str(result['location_id']) + ' ' + str(result['location_name'])))
  cursor.close()

  context = dict(data = restaurants)
  
  if request.method == 'GET':
    return render_template("register.html", **context)
  
  if request.method == 'POST':
    name = request.form['name']
    username = request.form['username']
    password = request.form['password']
    confirm_password = request.form['confirm-password']
    email = request.form['email']
    dob = request.form['dob']
    employee = request.form.getlist('employee')
    location_id = request.form.get('locations').split()[0]
    
    # Check username length
    if len(username) < 1:
      flash('Username is required')
      return render_template('register.html', **context)
    
    # Confirm passwords
    if password != confirm_password:
      flash('Passwords do not match')
      return render_template('register.html', **context)

    # Check password length
    if len(password) < 8:
      flash('Password must contain at least 8 characters')
      return render_template('register.html', **context)

    # Check availability of username
    cmd = 'SELECT * FROM users WHERE username = (:username)';
    cursor = g.conn.execute(text(cmd), username = username);
    users = []
    for result in cursor:
      users.append(result['user_id'])
    cursor.close()

    if len(users) != 0:
      flash('Username already in use')
      return render_template('register.html', **context)
    
    # FIXME remove print when deployed
    print("""name: {}, username: {}, password: ********,
        email: {}, dob:{}""".format(name, username, email, dob))

    # Insert new user
    dt = datetime.now()
    cmd = """INSERT INTO users(user_name, username, user_password, join_date)
        VALUES (:name, :username, :password, :join_date)""";
    g.conn.execute(text(cmd), name=name, username=username, password=password, join_date=dt);

    # Get user_id
    cmd = 'SELECT * FROM users WHERE username = (:username)';
    cursor = g.conn.execute(text(cmd), username = username);
    for result in cursor:
      user_id = result['user_id']
    cursor.close()
    
    # Insert new customer
    cmd = """INSERT INTO customer VALUES (:user_id, :dob, :email)""";
    g.conn.execute(text(cmd), user_id=user_id, dob=dob, email=email);

    # Insert new employee
    if len(employee) > 0:
      cmd = 'INSERT INTO employeeof VALUES (:user_id, NULL, :location_id)';
      g.conn.execute(text(cmd), user_id=user_id, location_id=location_id);

    # Format registration successful flash
    if len(employee) > 0:
      flash('User and employee registration successful: employee of {}'.format(location_id))
    else:
      flash('User registration successful')
    return render_template("login.html")
  else:
    return render_template("register.html", **context)


@app.route('/login', methods=['POST'])
def login():
  username = request.form['username']
  password = request.form['password']
  
  # FIXME remove print when deployed
  print('username: {}, password: ********'.format(username))
  
  cmd = 'SELECT * FROM users WHERE username = (:username) AND user_password = (:password)';
  cursor = g.conn.execute(text(cmd), username = username, password = password);
  users = []
  for result in cursor:
    users.append(result['user_id'])
  cursor.close()

  if len(users) != 0:
    session['logged_in'] = True
    session['user_id'] = users[0]
  else:
    flash('Wrong password')
  return index()


@app.route('/logout')
def logout():
  session['logged_in'] = False
  session.pop('user_id', None)
  return index()


@app.route('/<string:user_id>/orderhistory', methods=['GET', 'POST'])
def orderhistory(user_id):
  if not session.get('logged_in'):
    return render_template('login.html')
  else:

    cmd = """
    SELECT o.order_id, o.order_item_id, o.menu_item_name, o.quantity, r.location_name, o.order_placed, o.rating 
    FROM placed p, ordered o, restaurant r
    WHERE p.customer_id = :user_id AND p.order_id = o.order_id
    AND o.location_id = r.location_id """;
    cursor = g.conn.execute(text(cmd), user_id=user_id);

    orders = []
    for result in cursor:
      orders.append(dict(order_id=result['order_id'],
                         order_item_id=result['order_item_id'],
                         menu_item_name=result['menu_item_name'],
                         quantity=result['quantity'],
                         location_name=result['location_name'],
                         order_placed=result['order_placed'],
                         rating=result['rating']))
    cursor.close()

    context = dict(orders=orders)
    if request.method == 'GET':
      return render_template('orderhistory.html', **context)
    else:
      # used to identify every 3 terms (order_id, order_item_id, rating)
      cur_order_id = None
      cur_order_item_id = None
      cur_rating = None
      rating_list = request.form.getlist('rating')
      for ind, entry in enumerate(rating_list):
        if ind % 3 == 2: # rating
          if entry != '':
            cur_order_id = rating_list[ind - 2]
            cur_order_item_id = rating_list[ind - 1]
            cur_rating = entry
            for d in orders:
              if d['order_id'] == cur_order_id and d['order_item_id'] == cur_order_item_id:
                d['rating'] = cur_rating
            # Update Command
            cmd = """UPDATE ordered SET rating= :rating 
            WHERE order_id= :order_id AND order_item_id= :order_item_id""";
            g.conn.execute(text(cmd), rating=cur_rating, order_id=cur_order_id,
                           order_item_id=cur_order_item_id);

      context_updated = dict(orders=orders)
      return render_template('orderhistory.html', **context_updated)


# View orders awaiting pickup and already picked up
# Mark and unmark orders as picked up
@app.route('/<string:location_id>/pickup', methods=['GET', 'POST'])
def pickup(location_id):
  if not session.get('logged_in'):
    return render_template('login.html')
  else:
    # Query for location_name
    cmd = "SELECT location_name FROM restaurant WHERE location_id = :location_id";
    cursor = g.conn.execute(text(cmd), location_id = location_id);

    for result in cursor:
      location_name = result['location_name']
    cursor.close()

    # Get orders that have not been picked up
    cmd = """WITH DistinctOrders AS (
        SELECT o.pickup, o.order_id, o.order_item_id, p.customer_id, p.date_placed,
        ROW_NUMBER() OVER (PARTITION BY o.order_id) AS rownum
        FROM placed p, ordered o
        WHERE p.order_id = o.order_id AND o.pickup = 'true' AND o.location_id = :location_id AND
        (o.order_id, o.order_item_id) NOT IN (SELECT order_id, order_item_id FROM pickupBy)
        ) SELECT * FROM DistinctOrders WHERE rownum = 1
    """;
    cursor = g.conn.execute(text(cmd), location_id = location_id);
    to_pickup = []
    for result in cursor:
      placed_dt = '{0:%Y-%m-%d %H:%M:%S}'.format(result['date_placed'])
      to_pickup.append(dict(pickup=result['pickup'], order_id=result['order_id'],
                            order_item_id=result['order_item_id'], customer_id=result['customer_id'],
                            date_placed=placed_dt))
    cursor.close()
    
    # Get orders that have been picked up TODO test
    cmd = """WITH DistinctOrders AS (
        SELECT o.pickup, o.order_id, o.order_item_id, p.customer_id, p.date_placed, pB.pickup_time,
        ROW_NUMBER() OVER (PARTITION BY o.order_id) AS rownum
        FROM placed p, ordered o, pickupBy pB
        WHERE p.order_id = o.order_id AND p.order_id = pB.order_id AND
        o.location_id = :location_id AND o.pickup = 'true'
        ) SELECT * FROM DistinctOrders WHERE rownum = 1
    """;
    cursor = g.conn.execute(text(cmd), location_id = location_id);
    were_pickup = []
    for result in cursor:
      pickup_dt = '{0:%Y-%m-%d %H:%M:%S}'.format(result['pickup_time'])
      were_pickup.append(dict(pickup=result['pickup'], order_id=result['order_id'],
                              order_item_id=result['order_item_id'], customer_id=result['customer_id'],
                              date_placed=result['date_placed'], pickup_time=pickup_dt))
    
    context = dict(location_id=location_id, location_name=location_name, to_pickup=to_pickup,
                   were_pickup=were_pickup)

    if request.method == 'GET':
      return render_template('pickup.html', **context)

    if request.method == 'POST':
      update_to_pickup = request.form.getlist('to_pickup-box')
      update_were_pickup = request.form.getlist('were_pickup-box')
      
      dt = datetime.now()
      conf_msg = ''
      
      n_to_pickup = 0
      orders_marked_pickup = []
      # Add orders to pickupBy
      for order in update_to_pickup:
        idx = int(order.split('-')[0])
        order_info = to_pickup[idx]
        
        cmd = "INSERT INTO pickupBy VALUES (:customer_id, :order_id, :order_item_id, :pickup_time)";
        g.conn.execute(text(cmd), customer_id=order_info['customer_id'], order_id=order_info['order_id'],
                       order_item_id=order_info['order_item_id'], pickup_time=dt);
        n_to_pickup += 1
        # Update pickup time
        order_info['pickup_time'] = dt
        orders_marked_pickup.append(order_info)

      n_were_pickup = 0
      orders_unmarked_pickup = []
      # Remove orders from pickupBy
      for order in update_were_pickup:
        idx = int(order.split('-')[0])
        order_info = were_pickup[idx]
        
        cmd = "DELETE FROM pickupBy WHERE order_id = :order_id AND order_item_id = :order_item_id";
        g.conn.execute(text(cmd), order_id=order_info['order_id'],
                       order_item_id=order_info['order_item_id']);
        n_were_pickup += 1
        orders_unmarked_pickup.append(order_info)

      # Update context
      for order in orders_marked_pickup:
        to_pickup.remove(order)
        were_pickup.append(order)
      for order in orders_unmarked_pickup:
        were_pickup.remove(order)
        to_pickup.append(order)
      
      flash('Marked {} items as picked up'.format(n_to_pickup))
      flash('Unmarked {} items as picked up'.format(n_were_pickup))
      return render_template('pickup.html', **context)


# View sales statistics
@app.route('/<string:location_id>/dashboard', methods=['GET', 'POST'])
def dashboard(location_id):
  if not session.get('logged_in'):
    return render_template('login.html')
  else:
    # Total Sales Last week

    cmd = """
    WITH order_info AS (
      SELECT o.order_id, o.order_item_id, o.quantity
      FROM ordered o
      WHERE o.location_id= :location_id AND o.order_placed > (CURRENT_DATE - INTEGER '7')
    )
    SELECT ROUND(SUM(oi.quantity * i.menu_item_price)) AS total_sales
    FROM order_info oi, item i
    WHERE oi.order_item_id = i.item_id
    """;
    cursor = g.conn.execute(text(cmd), location_id=location_id);
    sales = []
    for result in cursor:
      sales.append(dict(total_sales=result['total_sales']))
    cursor.close()

    # Sales Per Order
    cmd = """
    WITH order_info AS (
      SELECT o.order_id, o.order_item_id, o.quantity
      FROM ordered o
      WHERE o.location_id= :location_id AND o.order_placed > (CURRENT_DATE - INTEGER '7')
    )
    SELECT SUM(oi.quantity * i.menu_item_price) / COUNT(DISTINCT(oi.order_id)) AS sales_per_order
    FROM order_info oi, item i
    WHERE oi.order_item_id = i.item_id
    """;
    cursor = g.conn.execute(text(cmd), location_id=location_id);
    sales_per_order = []
    for result in cursor:
      sales_per_order.append(dict(sales_per_order=result['sales_per_order']))
    cursor.close()

    # Popular items top 3
    cmd = """
    WITH order_info AS (
      SELECT o.order_id, o.order_item_id, o.quantity
      FROM ordered o
      WHERE o.location_id= :location_id AND o.order_placed > (CURRENT_DATE - INTEGER '7')
    ), tmp AS (
      SELECT oi.order_item_id as item_id, SUM(oi.quantity) as quantity
      FROM order_info oi
      GROUP BY oi.order_item_id
      ORDER BY quantity DESC
      LIMIT 3
    )
    SELECT i.menu_item_name, tmp.quantity
    FROM tmp, item i
    WHERE tmp.item_id = i.item_id
    """;

    cursor = g.conn.execute(text(cmd), location_id=location_id);
    popular_items = []
    for result in cursor:
      popular_items.append(dict(item_name=result['menu_item_name'], quantity=result['quantity']))
    cursor.close()
    context = dict(location_id=location_id, sales=sales, sales_per_order=sales_per_order,
                   popular_items=popular_items)
    return render_template('dashboard.html', **context)


if __name__ == "__main__":
  import click
  app.secret_key = os.urandom(12)
  
  @click.command()
  @click.option('--debug', is_flag=True)
  @click.option('--threaded', is_flag=True)
  @click.argument('HOST', default='0.0.0.0')
  @click.argument('PORT', default=8111, type=int)
  def run(debug, threaded, host, port):
    """
    This function handles command line parameters.
    Run the server using

        python server.py

    Show the help text using

        python server.py --help

    """

    HOST, PORT = host, port
    print("running on %s:%d" % (HOST, PORT))
    app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)
    

  run()
