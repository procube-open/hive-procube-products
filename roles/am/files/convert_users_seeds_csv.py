import sys
import csv

def make_idm_csv():
  input_csv = sys.argv[1]
  output_csv = sys.argv[2]

  update_user_dict = {}
  with open(input_csv, 'r') as in_f:
    reader = csv.reader(in_f)
    counter = 0
    for row in reader:
      counter+=1
      if len(row) < 3:
        logging("Invalid row: " + counter + ", skipping.")
        continue


      uid = row[0]
      seed = row[1]
      dt = row[2]
      dotpos = dt.find(".")
      if dotpos > 0:
        dt = dt[0:dotpos]

      if uid in update_user_dict:
        dt_prev = update_user_dict[uid]
        if dt < dt_prev:
          update_user_dict[uid] = dt
      else:
        update_user_dict[uid] = dt


  with open(output_csv, 'w') as out_f:
    writer = csv.writer(out_f, quoting=csv.QUOTE_ALL)

    for k,v in update_user_dict.items():
      output_row = ["M", k, v]
      writer.writerow(output_row)


if __name__ == '__main__':
    make_idm_csv()

