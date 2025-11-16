# TODO: Remove JSON Operations and Use Only MySQL

## Information Gathered
- The application currently stores data in both MySQL and JSON files.
- JSON files are only needed for auto-uploading to Railway volume.
- Need to remove all JSON file operations for data storage and use only MySQL.
- Categories are in categories.json, but Category table exists in MySQL.
- Locations and visuals save to both JSON and MySQL.
- FAQs have JSON fallback in admin_faqs.

## Plan
1. Update admin_faqs to remove JSON fallback code.
2. Remove JSON operations from add_info, edit_info, delete_info routes.
3. Remove JSON operations from location routes (add_location, edit_location, delete_location).
4. Remove JSON operations from visual routes (add_visual, edit_visual, delete_visual).
5. In chatbot.py, remove save_location_rules, save_visual_rules, and JSON operations in delete_rule.
6. Update add_category, remove_category, get_categories to use MySQL Category table instead of categories.json.
7. Update admin_existing_locations and admin_existing_visuals to remove JSON code.
8. Update auto_upload_json_files to generate JSON files from MySQL data before uploading to Railway.
9. Ensure all data loading is from MySQL only.

## Dependent Files to be edited
- app.py: Remove JSON operations in routes, update category functions.
- chatbot.py: Remove JSON saving methods.
- models.py: Ensure Category model is used.
- chatbot_models.py: Already has Category model.

## Followup steps
- Test that all admin operations work with MySQL only.
- Verify Railway upload still works with generated JSON.
- Remove any unused JSON files after migration.
