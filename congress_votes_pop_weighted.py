import sys
import csv
import requests


def main():

  state_information = get_state_information('state_population.csv')

  senate_totals = get_vote_totals('senate', 115, state_information)

  write_totals('senate_results.csv', senate_totals)

  house_totals = get_vote_totals('house', 115, state_information)

  write_totals('house_results.csv', house_totals)


#####################################################################
#
#
#####################################################################
def get_state_information(file_path):

  state_information = dict()

  with open(file_path) as popfile:

    reader = csv.DictReader(popfile)
    population_total = 0

    for row in reader:

      state_information[row['short_state']] = {
        'population':       int(row['2017_population']),
        'representatives':  int(row['representatives']),
      }

      population_total += int(row['2017_population'])

    for key in state_information.keys():
      state_information[key]['pop_percent'] = state_information[key]['population'] / population_total

  return state_information


#####################################################################
#
#
#####################################################################
def get_vote_totals(chamber, congress, state_information):

  url_format = "https://api.propublica.org/congress/v1/%s/%s/sessions/%d/votes/%d.json"
  headers = dict()

  with open('propublica_api_key.txt') as key_file:
    headers['X-API-Key'] = key_file.readline()

  vote_totals = []
  for session in [1, 2]:

    roll_call = 1
    while True:

      print(roll_call)
      r = requests.get(
        url = url_format % (congress, chamber, session, roll_call),
        headers = headers
      )

      data = r.json()

      if data['status'] == 'OK':
        vote_totals.append(
          process_data(
            data["results"]["votes"]["vote"],
            state_information,
            chamber
          )
        )
      else:
        break

      roll_call += 1

  return vote_totals


#####################################################################
#
#
#####################################################################
def process_data(data, state_information, chamber):

  result = {
    "congress":         data['congress'],
    "session":          data['session'],
    "roll_call":        data['roll_call'],
    "chamber":          data['chamber'],
    "result":           data['result'],
    "yes_population" :  0,
    "no_population" :   0,
    "yes_congress" :    0,
    "no_congress" :     0,
    "other_congress" :  0,
  }

  for vote in data["positions"]:

    representatives = 2 if chamber == 'senate' else state_information[vote['state']]['representatives']

    rep_vote_weighted = state_information[vote["state"]]['pop_percent'] / representatives

    if vote["vote_position"] == 'Yes':
      result["yes_population"] += rep_vote_weighted
      result["yes_congress"] += 1

    elif vote["vote_position"] == 'No':
      result["no_population"] += rep_vote_weighted
      result["no_congress"] += 1

    else:
      result['other_congress'] += 1

  result["other_population"] = 1 - (result["yes_population"] + result["no_population"])

  return result


#####################################################################
#
#
#####################################################################
def write_totals(file, totals):

  with open(file, 'w', newline='') as resultfile:

    writer = csv.DictWriter(resultfile, fieldnames=totals[0].keys())

    writer.writeheader()

    for vote in totals:
      writer.writerow(vote)


# if running as script
if __name__ == "__main__":
  main()
