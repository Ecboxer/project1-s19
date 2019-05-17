@app.route('/<string:location_id>/updatedeleteitem', methods=['GET', 'POST'])
def updatedeleteitem(location_id):
  if not session.get('logged_in'):
    return render_template('login.html')
  else:
    # TODO Refresh item display info after form submit
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
      return render_template('updatedeleteitem.html', **context)

    if request.method == 'POST':
      delete_boxes = request.form.getlist('delete-box')
      update_boxes = request.form.getlist('update-box')
      menu_sections = request.form.getlist('menu-section')
      item_names = request.form.getlist('menu-item-name')
      item_descriptions = request.form.getlist('menu-item-description')
      attribute_names = request.form.getlist('menu-attribute-name')
      item_prices = request.form.getlist('update-item-price')

      # Find items selected for delete/update
      delete_items = [int(x.split('-')[0]) for x in delete_boxes]
      update_items = [int(x.split('-')[0]) for x in update_boxes]

      # Check that no items were selected for both
      delete_and_update = [x for x in delete_items if x in update_items]
      if len(delete_and_update) > 0:
        flash('Warning: You may select either Delete or Update for any item, but not both')
        render_template('updatedeleteitem.html', **context)

      # Check that no deleted items had updated content
      for item_idx in delete_items:
        if len(menu_sections[item_idx]) > 0 or len(item_names[item_idx]) > 0 or len(item_descriptions[item_idx]) > 0 or len(attribute_names[item_idx]) > 0 or len(item_prices[item_idx]) > 0:
          flash('Warning: Please do not select Delete and enter menu information for the same item')
          render_template('updatedeleteitem.html', **context)

      # Check that updated items have updated content
      for item_idx in update_items:
        if len(menu_sections[item_idx]) == 0 and len(item_names[item_idx]) == 0 and len(item_descriptions[item_idx]) == 0 and len(attribute_names[item_idx]) == 0 and len(item_prices[item_idx]) == 0:
          flash('Warning: Please enter item information for updated items or select Delete to remove an item')
          render_template('updatedeleteitem.html', **context)

      n_updated = 0
      # Update items
      for i, item_idx in enumerate(update_items):
        item_id = update_boxes[i].split('-')[2]
        if len(menu_sections[item_idx]) > 0:
          cmd = 'UPDATE item SET menu_section_name = :menu_section WHERE item_id = :item_id';
          g.conn.execute(text(cmd), menu_section=menu_sections[item_idx], item_id=item_id)
        if len(item_names[item_idx]) > 0:
          cmd = 'UPDATE item SET menu_item_name = :item_name WHERE item_id = :item_id';
          g.conn.execute(text(cmd), item_name=item_names[item_idx], item_id=item_id)
        if len(item_descriptions[item_idx]) > 0:
          cmd = 'UPDATE item SET menu_item_description = :item_description WHERE item_id = :item_id';
          g.conn.execute(text(cmd), item_description=item_descriptions[item_idx], item_id=item_id)
        if len(attribute_names[item_idx]) > 0:
          cmd = 'UPDATE item SET attribute_name = :attribute_name WHERE item_id = :item_id';
          g.conn.execute(text(cmd), attribute_name=attribute_names[item_idx], item_id=item_id)
        if len(item_prices[item_idx]) > 0:
          cmd = 'UPDATE item SET menu_item_price = :item_price WHERE item_id = :item_id';
          g.conn.execute(text(cmd), item_price=item_prices[item_idx], item_id=item_id)
        n_updated += 1

      # n_deleted = 0
      # # Delete items
      # for i, item_idx in enumerate(delete_items):
      #   item_id = delete_boxes[i].split('-')[2]
      #   cmd = 'DELETE FROM item WHERE item_id = :item_id';
      #   g.conn.execute(text(cmd), item_id=item_id)
      #   n_deleted += 1
      
      flash('Number Updated: ' + str(n_updated)) # + ' Number Deleted: ' + str(n_deleted))
      return render_template('updatedeleteitem.html', **context)
