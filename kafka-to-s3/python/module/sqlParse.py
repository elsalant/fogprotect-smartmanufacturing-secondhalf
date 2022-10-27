import sqlparse
import re

joinAdded = False

# returns the reformulated query and a dictionary of original column names with their aliases in the event
# redaction is required
def reformulateQuery(origQuery, extraWhere, extraJoins):
    global joinAdded
    # Run through the query.  Keep the SELECT and FROM clauses as-is.
    # JOIN..ON needs to be supplemented with whatever is passed as an extraJoin
    # WHERE (which does not appear as a keyword) needs to be supplemented by the extraWhere
    rebuiltQuery = ''
    tokens = sqlparse.parse(origQuery)[0]
    for index in range(0, len(tokens.tokens)):
        token = tokens[index]
        if token.is_keyword and token.value.casefold() == 'JOIN'.casefold() and joinAdded == False:
            joinAdded = True
            if extraJoins:
                rebuiltQuery += extraJoins +'\n'
            rebuiltQuery += token.value
  #          rebuiltQuery += modifyJoin(origQuery, extraJoins)
        elif re.search('where', token.value, re.IGNORECASE):  # first add the extraWhere, stripping out "WHERE" in original token
                if extraWhere:
                    rebuiltQuery += 'WHERE ' + extraWhere + ' AND ' + re.sub('where', '', token.value, flags=re.IGNORECASE)
                else:
                    rebuiltQuery += token.value
        else:
            rebuiltQuery += token.value

    # Now, check to see if the SELECT clause used any aliases (i.e. "AS")
    selectQuery = getSelectCondition(origQuery)
    if selectQuery:
        aliasDict = getSubstitutions(selectQuery)
    return rebuiltQuery, aliasDict

def getSelectCondition(origQuery):
    tokens = sqlparse.parse(origQuery)[0]
    #Get the "SELECT" statement and see if there are any "AS" subsitutions
    index = 0
    selectClause = ''
    for token in tokens:
        if str(token.ttype) == 'Token.Keyword.DML' and token.value.upper() == 'SELECT':
            while tokens[index+1].is_whitespace:
                index += 1
            selectClause = tokens[index+1].value
            break
        index += 1
    if selectClause == '':
        print('ERROR - no SELECT found')
    print('found SELECT clause')
    return selectClause


#Returns a dictionary of original column names and their aliases.  Note that
def getSubstitutions(selectClause):
    splitClause = selectClause.split(',')
    aliasDict = {}  # dictionary of aliases
    for element in splitClause:
        if ' AS '.casefold() in element.casefold():
            parts = re.split(' AS ' ,element, flags=re.IGNORECASE)
            aliasDict[parts[0].strip()] = parts[1].strip()
    return aliasDict


if __name__ == '__main__':
    query = "SELECT a.height as h, b.weight as w \nFROM tableA \nJOIN b on b.id = a.id \nWHERE a.height > 200"
    whereClause = " c.consent = 'True' "
    extraJoins = "JOIN c on c.id = a.id"
    redactDict = []
    newQuery, redactDict = reformulateQuery(query, whereClause, extraJoins)
    print(newQuery)
    print(redactDict)
