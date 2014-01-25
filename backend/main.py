import collections
from flask import Flask, jsonify, request
import models
import urllib
app = Flask(__name__)

import logging

@app.route('/')
def hello_world():
    return 'Census Explorer'

@app.route('/upload/<constituency_area>/<sheet_name>/<table>/', methods = ['POST'])
def upload(constituency_area, sheet_name, table):
    import json
    import hashlib
    from models import *
    #return '%s %s %s' % (constituency_area, language, table)
    #return request.form['jsondata']
    #return jsonify(request.form)
    data = json.loads(str(request.form.keys()[0]))
    first_column_name = data['meta']['first_column_name']
    table_name = data['meta']['name']
    for d in data['data']:
        row = d.pop(first_column_name)
        for (k, v) in d.items():
            constituency_area = constituency_area.lower()
            language = {'sheet0': u'traditional',
                    'sheet1': u'simplified',
                    'sheet2': u'english'}[sheet_name]
            table = table_name #.decode('utf-8')
            #logging.warning(k)
            #logging.warning(type(k))
            column = k #.decode('utf-8')
            row = row #.decode('utf-8')
            value = v
            _info = (constituency_area, language, table, row, column, value)
            logging.warning(str(_info))
            ok = True

            if value == u'':
                # missing value
                ok = False

            if ok:
                _id = hashlib.md5((u'%s %s %s %s %s %s' % _info).encode('utf-8')).hexdigest()
                constituency_area_key = list(ConstituencyArea.query(ConstituencyArea.code == constituency_area))[0].key
                logging.warning(constituency_area_key)
                dp = Datapoint(id=_id, 
                        constituency_area=constituency_area_key,
                        language=language,
                        table=table,
                        column=column,
                        row=row,
                        value=value)
                logging.warning(dp)
                dp.put()
    return "OK"


def parse_argument(query_string):
    """
    Takes a raw query_string from the request parameters, and returns a
    list of url decoded strings that can be used in the filtering.

    If query_string is None, then returns None
    """
    if query_string is None:
        return None
    res = urllib.unquote_plus(query_string).split(',')
    return res


@app.route('/api')
def api():
    """
    API Endpoint for accessing the data
    Takes query parameters in order to filter the dataset down

    Arguments:
    ----------
    ca: constituency areas
        Comma separated string of CA codes -- "a01,a02", etc.

    table: table name
        Comma separated string of the tables requested.  Must be urlencoded - "ethnicity"

    row: row name
        Comma separated string of the rows.  Urlencoded - "chinese"

    column: column name
        Comma separated string of the columns.  Urlencoded - "male"

    options: 0 or 1
        If options 1, then the response also includes an "options" key that
        lists the possible values for unspecified columns to further narrow the data down

        If there are no parameters provided, then options is 1 by default, and no data is returned

    Returns:
    --------
    JSON response, of the form:
    {
        data: [
            {
                constituency_area: {
                    name: string,
                    code: string,
                    district: string
                },
                table: string,
                row: string,
                column: string
                value: float or None
            },
            ...
        ],
        options: {
            table: []
        }
    }


    """
    # Parse the arguments
    ca = parse_argument(request.args.get('ca', None))
    table = parse_argument(request.args.get('table', None))
    row = parse_argument(request.args.get('row', None))
    column = parse_argument(request.args.get('column', None))
    options = bool(int(request.args.get('options', 0)))

    # Incrementally build the query
    query = models.Datapoint.query()
    if ca is not None:
        # constituency_area is a KeyProperty, so we need to retrieve these separately
        ca_keys = [x.key for x in models.ConstituencyArea.query(models.ConstituencyArea.code.IN(ca)).fetch()]
        query = query.filter(models.Datapoint.constituency_area.code.IN(ca))
    if table is not None:
        query = query.filter(models.Datapoint.table.IN(table))
    if row is not None:
        query = query.filter(models.Datapoint.row.IN(row))
    if column is not None:
        query = query.filter(models.Datapoint.column.IN(column))

    res = {}

    # If the query was filtered, then get the data
    no_filters_provided = all([ca is None, table is None, row is None, column is None])
    if not no_filters_provided:
        res['data'] = [x.to_dict() for x in query.fetch()]

    if options or no_filters_provided:
        option_res = {}

        # Incrementally build the available options for other columns
        # We need to do this after building the initial query, since we
        # only want the options for columns that we didn't filter on

        # This method issues four queries, but will return fewer results in cases
        # When no filter parameters are provided.  Issuing one query with a projection
        # Will return all combinations of the distinct values
        if ca is None:
            # Not sure if this works
            tmp = [x.constituency_area for x in models.Datapoint.query(filters=query._Query__filters, projection=['constituency_area'], distinct=True).fetch()]
            tmp = models.ConstituencyArea.query(models.ConstituencyArea.key.IN(tmp))
            option_res['ca'] = [x.code for x in tmp]
        if table is None:
            tmp = models.Datapoint.query(filters=query._Query__filters, projection=['table'], distinct=True).fetch()
            option_res['table'] = [x.table for x in tmp]
        if row is None:
            tmp = models.Datapoint.query(filters=query._Query__filters, projection=['row'], distinct=True).fetch()
            option_res['row'] = [x.row for x in tmp]
        if column is None:
            tmp = models.Datapoint.query(filters=query._Query__filters, projection=['column'], distinct=True).fetch()
            option_res['column'] = [x.column for x in tmp]

        res['options'] = option_res

    return jsonify(**res)

if __name__ == '__main__':
    app.run(host="0.0.0.0")