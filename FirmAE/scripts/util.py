#!/usr/bin/env python3

import sys
import psycopg2
import hashlib
import os
import csv

def io_md5(target):
    blocksize = 65536
    hasher = hashlib.md5()

    with open(target, 'rb') as ifp:
        buf = ifp.read(blocksize)
        while buf:
            hasher.update(buf)
            buf = ifp.read(blocksize)
        return hasher.hexdigest()

def query_(query, psql_ip, mode):
    try:
        dbh = psycopg2.connect(database="firmware_%s" % mode,
                               user="firmadyne",
                               password="firmadyne",
                               host=psql_ip, port=6666)
        cur = dbh.cursor()
        cur.execute(query)
        return cur.fetchone()

    except:
        return None

def get_iid(infile, psql_ip, mode):
    value = os.getenv("NO_PSQL")

    if value == "1":
        firm = os.path.basename(infile)
        csv_file_path = "/FuzzPlanner/FirmAE/firm_db_%s.csv"%(mode)
        try:
            with open(csv_file_path, mode='r') as csvfile:
                csv_reader = csv.DictReader(csvfile)
                for row in csv_reader:
                    if row['firmware'] == firm:
                        return row['id']
            return ""
        except FileNotFoundError:
            return ""
        except Exception as e:
            return ""
    else:
        md5 = io_md5(infile)
        q = "SELECT id FROM image WHERE hash = '%s'" % md5
        image_id = query_(q, psql_ip, mode)

        if image_id:
            return image_id[0]
        else:
            return ""

def get_brand(infile, psql_ip, mode):
    value = os.getenv("NO_PSQL")

    if value == "1":
        firm = os.path.basename(infile)
        csv_file_path = "/FuzzPlanner/FirmAE/firm_db_%s.csv"%(mode)
        try:
            with open(csv_file_path, mode='r') as csvfile:
                csv_reader = csv.DictReader(csvfile)
                for row in csv_reader:
                    if row['firmware'] == firm:
                        return row['brand']
            return ""
        except FileNotFoundError:
            return ""
        except Exception as e:
            return ""
    else:
        md5 = io_md5(infile)
        q = "SELECT brand_id FROM image WHERE hash = '%s'" % md5
        brand_id = query_(q, psql_ip, mode)

        if brand_id:
            q = "SELECT name FROM brand WHERE id = '%s'" % brand_id
            brand = query_(q, psql_ip, mode)
            if brand:
                return brand[0]
            else:
                return ""
        else:
            return ""

def check_connection(psql_ip, mode):
    value = os.getenv("NO_PSQL")

    if value == "1":
        return 0
    else:
        try:
            dbh = psycopg2.connect(database="firmware_%s" % mode,
                                user="firmadyne",
                                password="firmadyne",
                                host=psql_ip, port=6666)
            dbh.close()
            return 0
        except:
            return 1

# command line
if __name__ == '__main__':
    [infile, psql_ip, mode] = sys.argv[2:5]
    if sys.argv[1] == 'get_iid':
        print(get_iid(infile, psql_ip, mode))
    if sys.argv[1] == 'get_brand':
        print(get_brand(infile, psql_ip, mode))
    if sys.argv[1] == 'check_connection':
        exit(check_connection(psql_ip, mode))
