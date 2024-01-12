from flask import Flask, render_template, request, redirect, url_for, session
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import gspread
from google.oauth2 import service_account
import pandas as pd

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'

# Flask-Login setup
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Sample User class for Flask-Login
class User(UserMixin):
    pass

@login_manager.user_loader
def load_user(user_id):
    if user_id in users:
        user = User()
        user.id = user_id
        return user
    return None

credentials = service_account.Credentials.from_service_account_file(
    "indian-legal-information-d6444bb36676.json",
    scopes=['https://www.googleapis.com/auth/spreadsheets']
)

spreadsheet_id = '1mmCbbVKES-ZyiziXhSQZldkJWGaRf2DYHVhkr1sjeyM'
client = gspread.authorize(credentials)
worksheet = client.open_by_key(spreadsheet_id).sheet1
closed_players_sheet = client.open_by_key(spreadsheet_id).get_worksheet(1)
players_sheet = client.open_by_key(spreadsheet_id).get_worksheet(2)

users = {
    'user1': {'password': 'password1', 'team_name': 'Team A'},
    'user2': {'password': 'password2', 'team_name': 'Team B'},
    # Add more users as needed
}

def load_players_from_sheets():
    players_data = players_sheet.get_all_values()
    players = []

    for player_row in players_data[1:]:
        player = {
            "name": player_row[0],
            "age": player_row[1],
            "role": player_row[2],
            "batting": player_row[3],
            "bowling": player_row[4],
            "base_price": (player_row[5])
        }
        players.append(player)

    return players

players = load_players_from_sheets()
bids = {}
closed_players = []
active_auction = None 

def load_data_from_sheets():
    global bids
    values = worksheet.get_all_values()

    if values:
        headers = values[0]
        for row in values[1:]:
            player = row[0]
            age = row[1]
            role = row[2]
            bid_info = {'bid_amount': row[1] if len(row) > 1 else 0, 'team_name': row[2] if len(row) > 2 else ''}
            bids[player] = {'age': age, 'role': role, 'bid_info': bid_info}
            

def load_closed_players_from_sheets():
    global closed_players
    try:
        closed_players = closed_players_sheet.col_values(1)[1:]  
    except IndexError:
        closed_players = []

load_data_from_sheets()
load_closed_players_from_sheets()

def update_google_sheets():
    worksheet.clear()
    closed_players_sheet.clear()

    header = ['Player','Bid Amount', 'Team Name']
    worksheet.append_row(header)
    closed_players_sheet.append_row(['Closed Players'])

    for player,bid_info in bids.items():
        row_data = [player,bid_info['bid_amount'], bid_info['team_name']]
        worksheet.append_row(row_data)

    for closed_player in closed_players:
        closed_players_sheet.append_row([closed_player])

    for closed_player in closed_players:
        closed_players_sheet.append_row([closed_player])

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username in users and password == users[username]['password']:
            user = User()
            user.id = username
            login_user(user)
            return redirect(url_for('auction'))

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/auctioneer', methods=['GET', 'POST'])
@login_required
def auctioneer():
    global active_auction

    if request.method == 'POST':
        selected_player = request.form.get('selected_player')
        if selected_player and selected_player in [player['name'] for player in players] and selected_player not in closed_players:
            active_auction = selected_player
    return render_template('auctioneer.html', players=[player for player in players if player['name'] not in closed_players], active_auction=active_auction)

@app.route('/close_auction', methods=['POST'])
@login_required
def close_auction():
    global active_auction, closed_players
    if active_auction:
        closed_players.append(active_auction)
        active_auction = None
        update_google_sheets()
    return redirect(url_for('auctioneer'))

@app.route('/auction', methods=['GET', 'POST'])
@login_required
def auction():
    global active_auction

    if active_auction and active_auction in closed_players:
        active_auction = None

    player = next((p for p in players if p['name'] == active_auction), None)

    if request.method == 'POST':
        bid_amount = int(request.form['bid'])
        if active_auction and player:
            if active_auction in bids:
                if bid_amount > bids[active_auction]['bid_amount']:
                    bids[active_auction] = {'bid_amount': bid_amount, 'team_name': users[current_user.get_id()]['team_name']}
            else:
                bids[active_auction] = {'bid_amount': bid_amount, 'team_name': users[current_user.get_id()]['team_name']}

            update_google_sheets()

    return render_template('auction_player.html', player=player, current_bid=bids.get(active_auction, {}))


@app.route('/sold')
def sold():
    # Assuming worksheet and players_sheet are your data sheets
    data = worksheet.get_all_records()
    players_data = players_sheet.get_all_records()

    team_filter = request.args.get('team')
    if team_filter:
        data = [row for row in data if row['Team Name'] == team_filter]

    # Convert data to pandas DataFrame
    df_data = pd.DataFrame(data)
    df_players = pd.DataFrame(players_data)

    # Merge dataframes based on the player name (primary key)
    merged_data = pd.merge(df_data, df_players, how='inner', left_on='Player', right_on='Player Name')

    # Calculate total bid amount from the merged dataframe
    total_bid_amount = merged_data['Bid Amount'].sum()

    # Convert merged data back to a list of dictionaries
    merged_data_list = merged_data.to_dict(orient='records')

    return render_template('main.html', data=merged_data_list, total_bid_amount=total_bid_amount)

@app.route('/unsold_players')
def unsold_players():
    data = worksheet.get_all_records()
    data_player_names = {row['Player'] for row in data}

    player_data = players_sheet.get_all_records()
    yet_player_names = {row['Player Name'] for row in player_data}

    unsold_players = data_player_names.symmetric_difference(yet_player_names)

    return render_template('unsold.html', data=unsold_players)

@app.route('/analytics')
def analytics():
    return render_template('analytics.html')

if __name__ == '__main__':
    app.run(debug=True)
