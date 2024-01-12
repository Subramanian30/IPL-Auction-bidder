# from flask import Flask, render_template, request
# import gspread
# from oauth2client.service_account import ServiceAccountCredentials
# from google.oauth2 import service_account

# app = Flask(__name__)
# credentials = service_account.Credentials.from_service_account_file("indian-legal-information-d6444bb36676.json",scopes=['https://www.googleapis.com/auth/spreadsheets'])
# spreadsheet_id = '1mmCbbVKES-ZyiziXhSQZldkJWGaRf2DYHVhkr1sjeyM'
# client = gspread.authorize(credentials)
# worksheet = client.open_by_key(spreadsheet_id).sheet1
# closed_players_sheet = client.open_by_key(spreadsheet_id).get_worksheet(1)

# @app.route('/sold')
# def sold():
#     # Get all values from the sheet
#     data = worksheet.get_all_records()

#     # Apply team name filter if provided in the URL
#     team_filter = request.args.get('team')
#     if team_filter:
#         data = [row for row in data if row['Team Name'] == team_filter]

#     # Calculate the total sum of bid amounts
#     total_bid_amount = sum(int(row['Bid Amount']) for row in data)
#     return render_template('main.html', data=data, total_bid_amount=total_bid_amount)

# @app.route('/unsold_players')
# def unsold_players():
#     # Get all values from the sheets
#     data = worksheet.get_all_records()
#     data_player_names = {row['Player'] for row in data}

#     closed_data = closed_players_sheet.get_all_records()
#     closed_player_names = {row['Closed Players'] for row in closed_data}

#     unsold_players = data_player_names.symmetric_difference(closed_player_names)

#     return render_template('unsold.html', data=unsold_players)

# @app.route('/analytics')
# def analytics():
#     return render_template('analytics.html')

# if __name__ == '__main__':
#     app.run(debug=True)
