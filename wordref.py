import json, requests, os.path, csv, sys, re
from bs4 import BeautifulSoup, NavigableString

DEFAULT_RESULTS_FILE_NAME = 'wordref_results.csv'
DEFAULT_MAX_RESULTS = 3

from_lang = 'fr'
to_lang = 'en'
search_term = ''

print('Enter the name of the file you\'d like the results to be saved to (leave blank for default = % s): '% DEFAULT_RESULTS_FILE_NAME, end='')
outfile = input();
if not outfile:
  outfile = DEFAULT_RESULTS_FILE_NAME

print('Enter the maximum number of results you want per query (leave blank for default = 3): ', end='')
try:
  max_results = int(input());
except:
  max_results = DEFAULT_MAX_RESULTS

def format_definition(element):
  word = element.contents[0] if isinstance(element.contents[0], NavigableString) else element.contents[0].text
  part_of_speech = element.find('i').text if element.find('i') else ''
  return '% s (% s)'% (word, part_of_speech)

def update_result(result, key, value):
  result[key].append(value)

def get_translations(url):
  req = requests.get(url, timeout=60)
  soup = BeautifulSoup(req.content, 'html.parser')

  #extract definition and example sentences
  translations = soup.select('tr .even, tr .odd')

  results = []

  for translation in translations:
    if len(results) == max_results:
      break

    if not results or translation['class'] != prev_class_attr:
      prev_class_attr = translation['class']
      if len(translation['class']) > 1:
        continue
      results.append({'from': [], 'to': [], 'from_ex': [], 'to_ex': []})

    #definitions have an id attribute (as opposed to example sentences)
    if translation.has_attr('id'):
      from_word = format_definition(translation.find(class_='FrWrd'))
      to_word = format_definition(translation.find(class_='ToWrd'))
      update_result(results[-1], 'from', from_word)
      update_result(results[-1], 'to', to_word)

    elif from_example := translation.find(class_='FrEx'):
      update_result(results[-1], 'from_ex', from_example.text)
    elif to_example := translation.find(class_='ToEx'):
      update_result(results[-1], 'to_ex', to_example.text)

  return results

def format_defs(words, examples):
  formatted = ''
  formatted += '; '.join(words)
  if examples:
    formatted += '\n'
    for example in examples:
      formatted += '"% s"\n'% example
  return formatted

#continuously accept input until user quits
while True:
  print('Enter your query, or enter \'\q\' to quit: ', end='')
  search_term = input()

  if search_term == '\q':
    print("A plus!")
    sys.exit(0)
  else:
    url = 'https://wordreference.com/' + from_lang + to_lang + '/' + search_term

    if not os.path.isfile(outfile):
      results_csv = open(outfile, 'x', newline='', encoding='utf-8')
      writer = csv.writer(results_csv, delimiter=',')
      header = [from_lang, to_lang]
      writer.writerow(header)
    else:
      results_csv = open(outfile, 'a', newline='', encoding='utf-8')
      writer = csv.writer(results_csv, delimiter=',')

    translations = get_translations(url)

    for translation in translations:
      frm = format_defs(translation['from'], translation['from_ex'])
      to = format_defs(translation['to'], translation['to_ex'])

      print(frm)
      print(to)
      print('\n********\n')

      writer.writerow([frm, to])

    results_csv.close()
