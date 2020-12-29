username = "RenoirTan"
password = "soyaduck"
cluster = "librarium-ipdc0"
database = "TestLibrary"
books = "books"
borrowers = "borrowers"
loans = "loans"
library = "library"

import bson
import datetime
import dns
import pprint
from time import process_time

iprint = pprint.PrettyPrinter(
    depth = 4
)

from librarium import Library

client = Library()
client.connect(
    username = username,
    password = password,
    cluster = cluster
)
client.connect_db(
    name = database,
    create = False
)
client.connect_col(
    create = True,
    books = books,
    borrowers = borrowers,
    loans = loans,
    library = library
)
iprint.pprint(client)
start = process_time()


#book_ids = client.import_books(
#    "books.json"
#)
#print(book_ids)


#books = client.search_books(
#    pub_date = [
#        {
#            "$lte": datetime.datetime(1988, 1, 1),
#            "$gte": datetime.datetime(1986, 1, 1)
#        }
#    ]
#)
#iprint.pprint(books)

#books = client.search_books(sort=[("name", 1)])
#iprint.pprint([book["name"] for book in books])


#borrower_ids = client.import_borrowers("borrowers.json", update=True)
#iprint.pprint(borrower_ids)


#borrowers = client.search_borrowers(sort = [("name", 1)])
#iprint.pprint(borrowers)


#borrower = client.search_borrowers(
#    username = "timtam"
#)[0]["_id"]
#details = client.delete_borrower(borrower)
#iprint.pprint(details)

#book = client.search_books(sort=)[0]["_id"]
#borrowed = client.book_borrowed(book)
#iprint.pprint(borrowed)


#borrower = client.search_borrowers(username="yamai")[0]["_id"]
#book = client.search_books(name="A Pickle")[0]["_id"]
#loan = client.add_loan(
#    book = book,
#    borrower = borrower,
#    begin_date = datetime.datetime.utcnow(),
#    end_date = {"year": 2020, "month": 8, "day": 15}
#)
#iprint.pprint(loan)


#details = client.return_loan(bson.objectid.ObjectId("5f096951e986f76648973a19"))
#iprint.pprint(details)


#loans = client.search_loans(
#    borrower = bson.objectid.ObjectId("5f096ef3795fc2b005c35add")
#)
#iprint.pprint(loans)

#borrower = client.get_borrower(
#    bson.objectid.ObjectId("5f093da5a893e6381d402bb4")
#)
#iprint.pprint(borrower)


#print(client.get_meta())


iprint.pprint(f"Time taken: {process_time()-start}s")
client.disconnect()
