import random
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
import os
import re

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# MySQL configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Jg$1/4/2023'
app.config['MYSQL_DB'] = 'ambassador_app'

mysql = MySQL(app)



@app.route('/')
def home():
    return render_template('login.html')



@app.route('/login', methods=['GET', 'POST'])
def login():

    session.clear()

    if request.method == 'POST':
        phone_number = request.form['phone_number']
        password = request.form['password']

        cursor = mysql.connection.cursor()
        cursor.execute('SELECT id, password FROM ambassadors WHERE phone_number = %s', [phone_number])
        user = cursor.fetchone()
        cursor.close()

        if not user:
            flash('No account found with that phone number.', 'error')
            return render_template('login.html')
        elif not check_password_hash(user[1], password):
            flash('Incorrect password, please try again', 'error')
            return render_template('login.html')
        else:
            session['user_id'] = user[0]
            return redirect(url_for('dashboard'))

    return render_template('login.html')



def generate_ambassador_code():
    words = [
        'love', 'hope', 'kind', 'care', 'gift', 'best', 'star', 'wise', 'glow', 'pure', 
        'calm', 'cool', 'bold', 'gold', 'warm', 'luck', 'free', 'hero', 'crew', 'dash', 
        'fair', 'lead', 'fast', 'good', 'safe', 'join', 'song', 'rich', 'ball', 'grow', 
        'heal', 'fine', 'rise', 'glad', 'cash', 'save', 'hawk', 'nice', 'rock', 'team', 
        'lift', 'clay', 'live', 'work', 'earn', 'stay', 'icon', 'move', 'flow', 'maze', 
        'gain', 'hall', 'leaf', 'kith', 'goal', 'peak', 'hand', 'aura', 'clip', 'fade', 
        'echo', 'dice', 'ever', 'bolt', 'dive', 'city', 'card', 'coal', 'nest', 'opal', 
        'open', 'pace', 'palm', 'park', 'path', 'aqua', 'chip', 'arch', 'roam', 'roar', 
        'ruby', 'rush', 'silk', 'soul', 'sure', 'sway', 'tall', 'push', 'town', 'wavy', 
        'lush', 'zone', 'wild', 'wink', 'well', 'wave', 'vast', 'vibe', 'view', 'vent', 
        'pull', 'nova', 'gaze', 'trap', 'toll', 'tint', 'tide', 'text', 'test', 'rift'
    ]

    while True:
        word = random.choice(words)
        digits = ''.join([str(random.randint(0, 9)) for _ in range(4)])
        
        ambassador_code = word + digits
        
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT COUNT(*) FROM ambassadors WHERE ambassador_code = %s', [ambassador_code])
        count = cursor.fetchone()[0]
        cursor.close()
        
        if count == 0:
            return ambassador_code
        


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    
    session.clear()

    if request.method == 'POST':
        name = request.form['name']
        phone_number = request.form['phone_number']

        phone_digits = ''.join(filter(str.isdigit, phone_number))
        if len(phone_digits) not in [10, 11]:
            flash('Phone number must be 10 or 11 digits long.', 'error')
            return render_template('signup.html')
        
        password = generate_password_hash(request.form['password'])
        ambassador_code = request.form['ambassador_code']
        referred_by = None
        default_avatar = 'avatar0.svg'  # Default avatar

        cursor = mysql.connection.cursor()

        cursor.execute('SELECT COUNT(*) FROM ambassadors WHERE phone_number = %s', [phone_number])
        phone_count = cursor.fetchone()[0]
        if phone_count > 0:
            flash('Phone number already exists. Please use a different phone number.', 'error')
            return render_template('signup.html')

        if ambassador_code:
            cursor.execute('SELECT COUNT(*) FROM ambassadors WHERE ambassador_code = %s', [ambassador_code])
            code_count = cursor.fetchone()[0]
            if code_count == 0:
                flash('Invalid ambassador code. Please enter a valid code or leave the field empty.', 'error')
                return render_template('signup.html')
            
            else:
                referred_by = ambassador_code

        regex = re.compile(r'^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*#?&/])[A-Za-z\d@$!%*#?&/|]{6,}$')        
        if not regex.match(request.form['password']):
            flash('Password must be at least 6 characters long and include at least 1 letter, 1 number, and 1 symbol.', 'error')
            return render_template('signup.html')   
             
        try:
            cursor.execute('''INSERT INTO ambassadors (name, phone_number, password, referred_by, commission, signup_date, avatar) 
                              VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP, %s)''', (name, phone_number, password, referred_by, 8, default_avatar))
            mysql.connection.commit()
            user_id = cursor.lastrowid  
            
            new_ambassador_code = generate_ambassador_code()
            cursor.execute('''UPDATE ambassadors SET ambassador_code = %s WHERE id = %s''', (new_ambassador_code, user_id))
            mysql.connection.commit()
            
            # Check the number of referrals and update commission if it reaches 5
            if referred_by:
                cursor.execute('SELECT COUNT(*) FROM ambassadors WHERE referred_by = %s', [referred_by])
                referral_count = cursor.fetchone()[0]
                if referral_count == 5:
                    cursor.execute('UPDATE ambassadors SET commission = 10 WHERE ambassador_code = %s', [referred_by])
                elif referral_count == 10:
                    cursor.execute('UPDATE ambassadors SET commission = 12 WHERE ambassador_code = %s', [referred_by])
                mysql.connection.commit()
            
            session['user_id'] = user_id  
        except mysql.connection.IntegrityError:
            flash('An error occurred during signup. Please try again.', 'error')
            return render_template('signup.html')        
        finally:
            cursor.close()

        return redirect(url_for('confirmation'))

    return render_template('signup.html')



@app.route('/confirmation')
def confirmation():
    if 'user_id' not in session:
        return redirect(url_for('home'))
    return render_template('confirmation.html')



@app.route('/select_avatar', methods=['GET', 'POST'])
def select_avatar():
    if 'user_id' not in session:
        return redirect(url_for('home'))

    user_id = session['user_id']
    cursor = mysql.connection.cursor()
    
    # Fetch user data (similar to other routes)
    cursor.execute('SELECT avatar FROM ambassadors WHERE id = %s', [user_id])
    user = cursor.fetchone()
    current_avatar = user[0] if user else 'avatar0.svg'

    if request.method == 'POST':
        if 'avatar' in request.form:
            avatar = request.form['avatar']
            cursor.execute('''UPDATE ambassadors SET avatar = %s WHERE id = %s''', (avatar, user_id))
            mysql.connection.commit()
        return redirect(url_for('generate_code'))

    cursor.close()

    # List all avatar images
    avatar_dir = os.path.join(app.static_folder, 'images/avatars')
    avatars = [f for f in os.listdir(avatar_dir) if os.path.isfile(os.path.join(avatar_dir, f))]
    avatars.sort(key=lambda x: int(x.replace('avatar', '').replace('.svg', '')))

    return render_template('select_avatar.html', avatars=avatars, current_avatar=current_avatar)



@app.route('/generate_code')
def generate_code():
    if 'user_id' not in session:
        return redirect(url_for('home'))

    user_id = session['user_id']
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT ambassador_code FROM ambassadors WHERE id = %s', [user_id])
    ambassador_code = cursor.fetchone()[0]
    cursor.close()

    return render_template('generate_code.html', ambassador_code=ambassador_code)



@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('home'))

    user_id = session['user_id']
    cursor = mysql.connection.cursor()
    
    # Fetch user's name, total earnings, and commission
    cursor.execute('SELECT name, total_earnings, commission, avatar, ambassador_code FROM ambassadors WHERE id = %s', [user_id])    
    user = cursor.fetchone()
    
    # Fetch number of referred ambassadors
    cursor.execute('SELECT COUNT(*) FROM ambassadors WHERE referred_by = (SELECT ambassador_code FROM ambassadors WHERE id = %s)', [user_id])
    num_referred_ambassadors = cursor.fetchone()[0]
    
    cursor.close()

    if user:
        full_name = user[0]
        first_name = full_name.split(' ')[0]  # Split and take the first part
        total_earnings = user[1]
        commission = user[2]
        avatar = user[3]
        ambassador_code = user[4]
    else:
        first_name = 'User'
        total_earnings = 0
        commission = 8  # Default commission if not found
        avatar = 'avatar0.svg'  # Default avatar if not found
        ambassador_code = 'N/A'

    total_earnings = f"{total_earnings:.2f}".rstrip('0').rstrip('.')
    commission = f"{commission:.2f}".rstrip('0').rstrip('.')

    return render_template('dashboard.html', name=first_name, total_earnings=total_earnings, num_referred_ambassadors=num_referred_ambassadors, commission=commission, avatar=avatar, ambassador_code=ambassador_code)



@app.route('/affiliates')
def affiliates():
    if 'user_id' not in session:
        return redirect(url_for('home'))

    user_id = session['user_id']
    cursor = mysql.connection.cursor()

    # Fetch the current user's ambassador code
    cursor.execute('SELECT ambassador_code, avatar FROM ambassadors WHERE id = %s', [user_id])
    user = cursor.fetchone()
    ambassador_code = user[0]
    user_avatar = user[1] if user[1] else 'avatar0.svg'   

    # Fetch the list of referred ambassadors
    cursor.execute('SELECT name, avatar, signup_date FROM ambassadors WHERE referred_by = %s ORDER BY signup_date DESC', [ambassador_code])
    referred_ambassadors_raw = cursor.fetchall()
    
    cursor.close()

    # Format the signup_date and calculate commission
    referred_ambassadors = []
    has_referrals = False
    for i, ambassador in enumerate(referred_ambassadors_raw):
        name = ambassador[0]
        avatar = ambassador[1]
        signup_date = ambassador[2].strftime('%B %d, %I:%M %p').lower()
        signup_date = signup_date.replace(" 0", " ", 1)  # Remove leading zero
        signup_date = signup_date.capitalize()  # Capitalize first letter

        referred_ambassadors.append((name, avatar, signup_date))
        has_referrals = True

    return render_template('affiliates.html', referred_ambassadors=referred_ambassadors, avatar=user_avatar, has_referrals=has_referrals)



@app.route('/leaderboard')
def leaderboard():
    if 'user_id' not in session:
        return redirect(url_for('home'))

    user_id = session['user_id']
    cursor = mysql.connection.cursor()

    # Fetch the current user's avatar
    cursor.execute('SELECT avatar FROM ambassadors WHERE id = %s', [user_id])
    user = cursor.fetchone()
    user_avatar = user[0] if user[0] else 'avatar0.svg'

    # Query to get the number of referred ambassadors for each ambassador
    cursor.execute('''
        SELECT a.name, a.avatar, COUNT(b.id) AS referred_count
        FROM ambassadors a
        LEFT JOIN ambassadors b ON a.ambassador_code = b.referred_by
        GROUP BY a.id
        ORDER BY referred_count DESC
    ''')
    leaderboard_data_raw = cursor.fetchall()
    cursor.close()

    total_entries = len(leaderboard_data_raw)
    premium_threshold = total_entries * 0.10
    gold_threshold = total_entries * 0.25
    silver_threshold = total_entries * 0.50

    leaderboard_data = []
    for index, entry in enumerate(leaderboard_data_raw):
        name = entry[0]
        avatar = entry[1] if entry[1] else 'avatar0.svg'
        referred_count = entry[2]

        if index < premium_threshold:
            css_class = 'diamond'
        elif index < gold_threshold:
            css_class = 'gold'
        elif index < silver_threshold:
            css_class = 'silver'
        else:
            css_class = ''

        leaderboard_data.append((name, avatar, referred_count, css_class))

    return render_template('leaderboard.html', leaderboard_data=leaderboard_data, user_avatar=user_avatar)





@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if 'user_id' not in session:
        return redirect(url_for('home'))

    user_id = session['user_id']
    cursor = mysql.connection.cursor()

    # Fetch the current user's data
    cursor.execute('SELECT name, avatar FROM ambassadors WHERE id = %s', [user_id])
    user = cursor.fetchone()
    name = user[0]
    avatar = user[1] if user[1] else 'avatar0.svg'

    cursor.close()

    return render_template('settings.html', name=name, avatar=avatar)

@app.route('/change_name', methods=['POST'])
def change_name():
    if 'user_id' not in session:
        return redirect(url_for('home'))

    user_id = session['user_id']
    new_name = request.form['new_name']

    cursor = mysql.connection.cursor()
    cursor.execute('UPDATE ambassadors SET name = %s WHERE id = %s', (new_name, user_id))
    mysql.connection.commit()
    cursor.close()

    flash('Name successfully updated.', 'success')
    return redirect(url_for('settings'))

@app.route('/change_password', methods=['POST'])
def change_password():
    if 'user_id' not in session:
        return redirect(url_for('home'))

    user_id = session['user_id']
    current_password = request.form['current_password']
    new_password = request.form['new_password']

    cursor = mysql.connection.cursor()
    cursor.execute('SELECT password FROM ambassadors WHERE id = %s', [user_id])
    stored_password = cursor.fetchone()[0]

    if not check_password_hash(stored_password, current_password):
        flash('Current password is incorrect.', 'error')
        return redirect(url_for('settings'))

    # Regular expression for strong password validation
    regex = re.compile(r'^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*#?&/])[A-Za-z\d@$!%*#?&/|]{6,}$')        

    if not regex.match(new_password):
        flash('Password must be at least 6 characters long and include at least 1 letter, 1 number, and 1 symbol.', 'error')
        return redirect(url_for('settings'))

    hashed_new_password = generate_password_hash(new_password)
    cursor.execute('UPDATE ambassadors SET password = %s WHERE id = %s', (hashed_new_password, user_id))
    mysql.connection.commit()
    cursor.close()

    flash('Password successfully updated.', 'success')
    return redirect(url_for('settings'))




@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))




if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)