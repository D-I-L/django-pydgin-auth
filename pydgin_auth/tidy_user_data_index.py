'''
Created on 25 Oct 2016

 This is a prototype piece of software that can be run on the command line that attempts to solve the issue of
 deleting different elastic search contexts. It requires elastic search 2.3.0 especially the reindex API.
 1. Check database to retrieve current contexts
 2. Work out current (source) index alias for user defined data
 3. Use 3 to work out destination index (flip between two choices based on 2).
 4. If 3 exists delete it.
 5. Reindex src index to dest index using just contexts from 1.
 6. Alter alias to point to dest.

@author: Oliver Burren
'''

import psycopg2
import urllib.request
import json
import re


def index_exists(eurl, idx):
    dreq = urllib.request.Request(elastic_url + '/' + idx, method='HEAD')
    try:
        urllib.request.urlopen(dreq)
    except urllib.error.HTTPError as err:
        if err.code == 404:
            print("Index does not disease")
            return False
    return True

def delete_index(eurl, idx):
    if index_exists(eurl, idx):
        dreq = urllib.request.Request(elastic_url + '/' + new_index_name, method='DELETE')
        try:
            urllib.request.urlopen(dreq)
        except urllib.error.HTTPError as err:
            if err.code == 404:
                print("Could not delete")
                return False
    return True


def create_index(eurl, idx):
    # check if index already exists if it does delete
    if index_exists(eurl, idx):
        delete_index(eurl, idx)
    data = {
            "settings": {
                         "index": {
                                  "number_of_shards": 5,
                                  "number of replicas": 1
                                  }
                         }
            }
    data = json.dumps(data)
    data = data.encode('utf8')
    req = urllib.request.Request(eurl + '/' + idx, data, method='PUT')
    with urllib.request.urlopen(req) as response:
        the_page = response.read()
        print(the_page)


def reindex(eurl, src_index, dest_index, ctypes):
    url = eurl + '/_reindex'
    values = {
              'source': {'index': src_index, 'type': ctypes},
              'dest': {'index': dest_index}
              }
    data = json.dumps(values)
    data = data.encode('utf8')
    req = urllib.request.Request(url, data)
    try:
        urllib.request.urlopen(req)
    except urllib.error.HTTPError as err:
        if err.code == 404:
            return False
    return True


def switch_alias(eurl, act ,old ,new):
    data = {
            "actions": [
                {
                    'remove': {'index': old, 'alias': act}
                },
                {
                    'add': {'index': new, 'alias': act}
                }
            ]
        }
    data = json.dumps(data)
    data = data.encode('utf8')
    req = urllib.request.Request(eurl + '/_aliases', data)
    try:
        urllib.request.urlopen(req)
    except urllib.error.HTTPError as err:
        if err.code == 404:
            return False
    return True


def get_current_alias(eurl, idx):
    url = eurl + idx + '/_alias'
    req = urllib.request.Request(url)
    try:
        response = urllib.request.urlopen(req)
    except urllib.error.HTTPError as err:
        if err.code == 404:
            print("Not found")
            return False
    obj = json.loads(response.read().decode('utf8'))
    return(list(obj)[0])

if __name__ == '__main__':
    elastic_url = 'http://localhost:9200/'
    index_name_alias = 'cp:hg19_userdata_bed'
    old_index_name = get_current_alias(elastic_url, index_name_alias)
    if old_index_name == 'cp:hg19_userdata_bed_v1':
        new_index_name = 'cp:hg19_userdata_bed_v2'
    else:
        new_index_name = 'cp:hg19_userdata_bed_v1'
    get_current_alias(elastic_url, index_name_alias)
    # warning this will blow away current index if it already exists
    create_index(elastic_url, new_index_name)
    # connect to database hard code for now but eventually these can come from the conf files
    conn = psycopg2.connect("dbname=chicp_authdb user=webuser")
    cur = conn.cursor()
    cur.execute("select model from django_content_type where model like 'cp_stats_ud-ud%'")
    cidx = cur.fetchall()
    print("Length is " + str(len(cidx)))
    if len(cidx) == 0:
        # random content_type that will never exist - effectively causes reindex to create blank index
        cidx = ['asdfdgsqwdfghghhjk']
    else:
        cidx = [re.sub("cp_stats_ud-ud-(.*)_idx_type", "\\1", i[0]) for i in cidx]
    # next we need to interface with elastic search to get a list of all the current mappings
    reindex(elastic_url, old_index_name, new_index_name, cidx)
    switch_alias(elastic_url, index_name_alias, old_index_name, new_index_name)
    pass
