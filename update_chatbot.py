import mysql.connector
import json
import os
import logging

class ChatbotDB:
    def __init__(self):
        # Use environment variables for MySQL connection, defaulting to Railway
        host = os.environ.get('MYSQL_HOST', 'trolley.proxy.rlwy.net')
        port = int(os.environ.get('MYSQL_PORT', '10349'))
        user = os.environ.get('MYSQL_USER', 'root')
        password = os.environ.get('MYSQL_PASSWORD', 'smxcYzdpwUJTAiRdJWQFPJNbfsbVTAGC')
        database = os.environ.get('MYSQL_DATABASE', 'railway')

        self.conn = mysql.connector.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database
        )
        self.cursor = self.conn.cursor(dictionary=True)

    def get_user_rules(self):
        self.cursor.execute("SELECT * FROM user_rules")
        return self.cursor.fetchall()

    def get_guest_rules(self):
        self.cursor.execute("SELECT * FROM guest_rules")
        return self.cursor.fetchall()

    def get_location_rules(self):
        """
        Get location rules from database and format them properly.
        Parses JSON questions and constructs HTML responses with images.
        """
        self.cursor.execute("SELECT * FROM locations")
        locations = self.cursor.fetchall()
        
        formatted_locations = []
        for loc in locations:
            # Parse JSON questions
            import json
            questions = json.loads(loc.get('questions', '[]')) if isinstance(loc.get('questions'), str) else loc.get('questions', [])
            urls = json.loads(loc.get('urls', '[]')) if isinstance(loc.get('urls'), str) else loc.get('urls', [])
            
            # Flatten questions if nested
            flattened_questions = []
            for q in questions:
                if isinstance(q, list):
                    flattened_questions.extend(q)
                elif isinstance(q, str):
                    flattened_questions.append(q)
            
            # Construct HTML response with images
            description = loc.get('description', '')
            response = description
            
            if urls:
                response += "<br>"
                for url in urls:
                    # Ensure proper path format
                    if not url.startswith('/static/'):
                        url = f"/static/{url}"
                    response += f"<img src='{url}' alt='Location Image' class='message-image'>"
            
            formatted_loc = {
                'id': loc.get('id'),
                'category': 'locations',
                'questions': flattened_questions,
                'question': ' '.join(flattened_questions) if flattened_questions else '',
                'response': response,
                'answer': response,
                'user_type': loc.get('user_type', 'both')
            }
            formatted_locations.append(formatted_loc)
        
        return formatted_locations

    def get_visual_rules(self):
        """
        Get visual rules from database and format them properly.
        Parses JSON questions and constructs HTML responses with images/videos.
        """
        self.cursor.execute("SELECT * FROM visuals")
        visuals = self.cursor.fetchall()
        
        formatted_visuals = []
        for vis in visuals:
            # Parse JSON questions
            import json
            questions = json.loads(vis.get('questions', '[]')) if isinstance(vis.get('questions'), str) else vis.get('questions', [])
            urls = json.loads(vis.get('urls', '[]')) if isinstance(vis.get('urls'), str) else vis.get('urls', [])
            
            # Flatten questions if nested
            flattened_questions = []
            for q in questions:
                if isinstance(q, list):
                    flattened_questions.extend(q)
                elif isinstance(q, str):
                    flattened_questions.append(q)
            
            # Construct HTML response with images/videos
            description = vis.get('description', '')
            response = description
            
            if urls:
                response += "<br>"
                for url in urls:
                    # Ensure proper path format
                    if not url.startswith('/static/'):
                        url = f"/static/{url}"
                    
                    # Check if it's a video or image
                    if url.lower().endswith(('.mp4', '.webm', '.ogg')):
                        response += f"<video src='{url}' controls class='message-video' style='max-width: 100%; height: auto;'></video>"
                    else:
                        response += f"<img src='{url}' alt='Visual Content' class='message-image'>"
            
            formatted_vis = {
                'id': vis.get('id'),
                'category': 'visuals',
                'questions': flattened_questions,
                'question': ' '.join(flattened_questions) if flattened_questions else '',
                'response': response,
                'answer': response,
                'user_type': vis.get('user_type', 'both')
            }
            formatted_visuals.append(formatted_vis)
        
        return formatted_visuals

    def get_faqs(self):
        """
        Get FAQs from database.
        """
        self.cursor.execute("SELECT * FROM faqs")
        faqs = self.cursor.fetchall()
        # Format FAQs to match expected structure
        formatted_faqs = []
        for faq in faqs:
            formatted_faqs.append({
                'id': faq.get('id', ''),
                'question': faq.get('question', ''),
                'answer': faq.get('answer', '')
            })
        return formatted_faqs
    
    def get_categories(self):
        """
        Get all categories from database.
        """
        self.cursor.execute("SELECT * FROM categories")
        return self.cursor.fetchall()
    
    def get_email_directory(self):
        """
        Get all email directory entries from database.
        """
        self.cursor.execute("SELECT * FROM email_directory")
        return self.cursor.fetchall()

    def add_rule(self, rule_type, rule_data):
        if rule_type == 'user':
            table = 'user_rules'
        elif rule_type == 'guest':
            table = 'guest_rules'
        else:
            return False

        self.cursor.execute(f"""
            INSERT INTO {table} (id, category, question, answer, user_type)
            VALUES (%s, %s, %s, %s, %s)
        """, (rule_data['id'], rule_data['category'], rule_data['question'], rule_data['answer'], rule_type))
        self.conn.commit()
        return True

    def delete_rule(self, rule_type, rule_id):
        if rule_type == 'user':
            table = 'user_rules'
        elif rule_type == 'guest':
            table = 'guest_rules'
        else:
            return False

        self.cursor.execute(f"DELETE FROM {table} WHERE id = %s", (rule_id,))
        self.conn.commit()
        return True

    def edit_rule(self, rule_type, rule_id, rule_data):
        if rule_type == 'user':
            table = 'user_rules'
        elif rule_type == 'guest':
            table = 'guest_rules'
        else:
            return False

        self.cursor.execute(f"""
            UPDATE {table}
            SET question = %s, answer = %s
            WHERE id = %s
        """, (rule_data['question'], rule_data['answer'], rule_id))
        self.conn.commit()
        return True

    def add_location(self, location_data):
        """
        Add a new location to the database.
        """
        self.cursor.execute("""
            INSERT INTO locations (id, questions, urls, description, user_type)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            location_data['id'],
            json.dumps(location_data['questions']),
            json.dumps(location_data['urls']),
            location_data['description'],
            location_data.get('user_type', 'both')
        ))
        self.conn.commit()
        return True

    def edit_location(self, location_id, location_data):
        """
        Edit an existing location in the database.
        """
        self.cursor.execute("""
            UPDATE locations
            SET questions = %s, urls = %s, description = %s, user_type = %s
            WHERE id = %s
        """, (
            json.dumps(location_data['questions']),
            json.dumps(location_data['urls']),
            location_data['description'],
            location_data.get('user_type', 'both'),
            location_id
        ))
        self.conn.commit()
        return True

    def delete_location(self, location_id):
        """
        Delete a location from the database.
        """
        self.cursor.execute("DELETE FROM locations WHERE id = %s", (location_id,))
        self.conn.commit()
        return True

    def add_visual(self, visual_data):
        """
        Add a new visual to the database.
        """
        self.cursor.execute("""
            INSERT INTO visuals (id, questions, urls, description, user_type)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            visual_data['id'],
            json.dumps(visual_data['questions']),
            json.dumps(visual_data['urls']),
            visual_data['description'],
            visual_data.get('user_type', 'both')
        ))
        self.conn.commit()
        return True

    def edit_visual(self, visual_id, visual_data):
        """
        Edit an existing visual in the database.
        """
        self.cursor.execute("""
            UPDATE visuals
            SET questions = %s, urls = %s, description = %s, user_type = %s
            WHERE id = %s
        """, (
            json.dumps(visual_data['questions']),
            json.dumps(visual_data['urls']),
            visual_data['description'],
            visual_data.get('user_type', 'both'),
            visual_id
        ))
        self.conn.commit()
        return True

    def delete_visual(self, visual_id):
        """
        Delete a visual from the database.
        """
        self.cursor.execute("DELETE FROM visuals WHERE id = %s", (visual_id,))
        self.conn.commit()
        return True

    def add_faq(self, faq_data):
        """
        Add a new FAQ to the database.
        """
        self.cursor.execute("""
            INSERT INTO faqs (question, answer)
            VALUES (%s, %s)
        """, (faq_data['question'], faq_data['answer']))
        self.conn.commit()
        return self.cursor.rowcount > 0

    def edit_faq(self, faq_id, faq_data):
        """
        Edit an existing FAQ in the database.
        """
        logging.info(f"Editing FAQ with ID: {faq_id}, data: {faq_data}")
        self.cursor.execute("""
            UPDATE faqs
            SET question = %s, answer = %s
            WHERE id = %s
        """, (faq_data['question'], faq_data['answer'], faq_id))
        self.conn.commit()
        affected_rows = self.cursor.rowcount
        logging.info(f"FAQ edit affected {affected_rows} rows")
        return affected_rows > 0

    def delete_faq(self, faq_id):
        """
        Delete an FAQ from the database.
        """
        self.cursor.execute("DELETE FROM faqs WHERE id = %s", (faq_id,))
        self.conn.commit()
        return self.cursor.rowcount > 0



    def close(self):
        self.cursor.close()
        self.conn.close()

# Test the DB class
if __name__ == '__main__':
    db = ChatbotDB()
    print("User rules:", len(db.get_user_rules()))
    print("Guest rules:", len(db.get_guest_rules()))
    print("Location rules:", len(db.get_location_rules()))
    print("Visual rules:", len(db.get_visual_rules()))
    print("FAQs:", len(db.get_faqs()))
    db.close()
