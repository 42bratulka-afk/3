import sqlite3

def init_db():
    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            tokens INTEGER DEFAULT 5,
            is_blocked INTEGER DEFAULT 0,
            is_admin INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

def register_or_update_user(user_id, username):
    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()
    clean_username = username.lstrip('@').lower() if username else None
    
    cursor.execute('SELECT user_id, tokens, is_blocked, is_admin FROM users WHERE user_id = ?', (user_id,))
    row = cursor.fetchone()
    if not row:
        cursor.execute(
            'INSERT INTO users (user_id, username, tokens, is_blocked, is_admin) VALUES (?, ?, 5, 0, 0)',
            (user_id, clean_username)
        )
    else:
        cursor.execute(
            'UPDATE users SET username = ? WHERE user_id = ?',
            (clean_username, user_id)
        )
    conn.commit()
    conn.close()

def get_user_by_identifier(identifier):
    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()
    
    str_id = str(identifier).strip()
    if str_id.isdigit():
        cursor.execute('SELECT user_id, username, tokens, is_blocked, is_admin FROM users WHERE user_id = ?', (int(str_id),))
    else:
        clean_username = str_id.lstrip('@').lower()
        cursor.execute('SELECT user_id, username, tokens, is_blocked, is_admin FROM users WHERE LOWER(username) = ?', (clean_username,))
        
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return None
    return {
        'user_id': row[0],
        'username': row[1],
        'tokens': row[2],
        'is_blocked': row[3],
        'is_admin': row[4]
    }

def modify_tokens(identifier, delta):
    user = get_user_by_identifier(identifier)
    if not user:
        return None, None
    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()
    new_tokens = max(0, user['tokens'] + delta)
    cursor.execute('UPDATE users SET tokens = ? WHERE user_id = ?', (new_tokens, user['user_id']))
    conn.commit()
    conn.close()
    return new_tokens, user['user_id']

def modify_status(identifier, field, value):
    user = get_user_by_identifier(identifier)
    if not user:
        return None
    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()
    cursor.execute(f'UPDATE users SET {field} = ? WHERE user_id = ?', (value, user['user_id']))
    conn.commit()
    conn.close()
    return user['user_id']
