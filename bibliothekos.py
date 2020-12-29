print("\n")
print("Welcome to Bibliothekos!".center(28))
print("\n")
print("Your Own Library Manager".center(28))
print("\n")
print("Type in 'help' for a list of commands.".center(21))

from bson.objectid import ObjectId
from datetime import datetime, timedelta
from getpass import getpass
import librarium
import re
from tabulate import tabulate

run = True

# CONNECT TO CLUSTER

try:
    from env import *
except ModuleNotFoundError as e:
    print("CRITICAL ERROR: Could not find environment variables file (env.py)")
    run = False
except AttributeError as e:
    print("CRITICAL ERROR: One of the variables in env.py has been deleted")
    print("or has had their name modified.")
    run = False

try:
    biblio = librarium.Library()
    biblio.connect(
        cluster = CLUSTER,
        username = USERNAME,
        password = PASSWORD
    )
    biblio.connect_db(
        name = DATABASE,
        create = False
    )
    biblio.connect_col(
        create = False,
        books = BOOKS,
        borrowers = BORROWERS,
        loans = LOANS,
        library = LIBRARY
    )
except TypeError as e:
    print("CRITICAL ERROR: One of the variables in env.py is not a string.")
    print("Make sure all the values for each variable is enclosed with 2")
    print('("").')
    run = False
except ValueError as e:
    print("ERROR: Your database or one of the collections has not been")
    print("created yet.")
except Exception as e:
    print("ERROR: Could not connect to your library cluster.")
    print("Please check your connection and your environment variables.")
    run = False
else:
    print("\nConnected to your library cluster.\n")


# LOCAL GLOBALS

borrower = None
borrower_data = None
admin = False

ASSISTANT = """
List of Commands:

login admin: Login as Admin.

logout admin: Logout from Admin. Run this when you allow the public to use the program.

exit admin: Exit from Bibliothekos.

login: Login as a normal borrower.

logout: Logout as a normal borrower.

new user: Create a new borrower account.

edit user: Edit data about your account.

search user: Get list of users and their IDs.

investigate user: Get a closer look on users based on their ID. Must be logged in as Admin.

delete self: Delete your account

about self: Get data about your account.

check loans: Check your outstanding loans.

borrow book: Borrow a book with its book ID.

return book: Return a book with the loan ID you have.

search books: Search for books.

add book: Add a book. Must be logged in as Admin.

delete book: Delete a book. Must be logged in as Admin.

edit book: Edit the information about a book. Must be logged in as Admin.

who borrowed: Find out who borrowed a book. Must be logged in as Admin.
"""


# FUNCTIONS

def admin_login():
    global admin
    global USERNAME
    global PASSWORD
    if admin:
        print("\nYou are already logged in as admin.\n")
        return None
    if (input("Admin Username |> ") == USERNAME and
        getpass("Admin Password |> ") == PASSWORD):
        admin = True
        print("\nLogged in as admin.\n")
        return None
    else:
        print("\nUsername or password is wrong.\n")
        return None

def admin_logout():
    global admin
    if admin:
        admin = False
    print("\nYou are now logged out from admin.\n")
    return None

def admin_exit():
    global biblio
    global USERNAME
    global PASSWORD
    global run
    if (input("Admin Username |> ") == USERNAME and
        getpass("Admin Password |> ") == PASSWORD):
        run = False
        biblio.disconnect()
        print("\nLibrary disconnected.\n")
    else:
        print("\nUsername or password is wrong.\n")

def user_login():
    global borrower
    global biblio
    global borrower_data
    if type(borrower) == ObjectId:
        print(
            f"\nYou are already logged in as {biblio.get_borrower(borrower)}.\n"
        )
        return None
    borrower_username = input("Please enter your username |> ")
    borrower_password = getpass("Please enter your password |> ")
    finding_id = biblio.find_borrowers(
        username = borrower_username,
        exact = True,
        insensitive = False
    )
    if len(finding_id) == 0:
        print("\nUsername or password is wrong.\n")
        return None
    data = biblio.get_borrower(objectid = finding_id[0])
    if data["password"] != borrower_password:
        print("\nUsername or password is wrong.\n")
        return None
    borrower = finding_id[0]
    borrower_data = data
    print(f"\nWELCOME, {data['name']}!")
    return None

def user_logout():
    global borrower
    global borrower_data
    if type(borrower_data) == dict:
        borrower = None
        print(f"\nGoodbye, {borrower_data['name']}. ;-;\n")
        borrower_data = None
    else:
        print("\nYou are not logged in yet.\n")
    return None

def user_create():
    global borrower
    global borrower_data
    global biblio
    if type(borrower) == ObjectId:
        print("\nPlease logout before creating a new account.\n")
        return None
    borrower_username = input("Select your username |> ")
    if len(biblio.find_borrowers(borrower_username, True, False)) > 0:
        print("\nAnother borrower with the same username already exists.\n")
        return None
    borrower_password = getpass("Create a password |> ")
    borrower_name = input("Enter your full name |> ")
    borrower_phone = input("Enter your phone number |> ")
    borrower_email = input("Enter your email |> ")
    borrower_address = input("Enter your address |> ")
    if input("Confirm details? (y/n) |> ") != "y":
        print("\nNew borrower account not created.\n")
        return None
    borrower = biblio.add_borrower(
        username = borrower_username,
        password = borrower_password,
        name = borrower_name,
        phone = borrower_phone,
        email = borrower_email,
        address = borrower_address
    )
    borrower_data = biblio.get_borrower(borrower)
    print(f"\nThanks for joining us, {borrower_name}!\n")

def user_update():
    global borrower
    global borrower_data
    global biblio
    if type(borrower) != ObjectId:
        print("\nPlease login first.\n")
        return None
    edit = True
    while edit:
        fields = ["name", "phone", "email", "address"]
        print("\nSelect the integer of any field to edit or exit:")
        print("\t1: name,")
        print("\t2: phone,")
        print("\t3: email,")
        print("\t4: address")
        print("\t5: exit")
        field = input("\n|> ")
        try:
            field = int(field)
        except Exception as e:
            print("\nYou did not enter an integer.\n")
            field = ""
            continue
        if field < 1 or field > 5:
            print("\nOption out of range. Try again.\n")
            continue
        if field == 5:
            edit = False
        value = input("\nValue |> ")
        biblio.update_borrower(borrower, **{fields[field-1]: value})
        print(f"\n{fields[field-1]} edited to {value}.\n")
    print("\nEdit successful.\n")
    return None

def user_search():
    global biblio
    terms = {}
    querying = True
    while querying:
        print("\nAdd, edit or delete queries with this format:")
        print("[update/delete/search/exit] [username/name]\n")
        item = input("|> ").split(" ")
        if item[0] in ["update", "delete"] and len(item) != 2:
            print("\nQuery command does not follow format.\n")
            continue
        if item[0] == "update":
            search_term = input("\nPlease enter search term |> ")
            if item[1] == "username":
                terms["username"] = search_term
            elif item[1] == "name":
                terms["name"] = search_term
            else:
                print(f"\nUnrecognised query item: {item[1]}\n")
        elif item[0] == "delete":
            deleted = terms.pop(item[1], item[1])
            print(f"Deleted query item: {deleted}")
        elif item[0] == "search":
            data = biblio.search_borrowers(**terms)
            print("\n")
            table_form = []
            for borrower in range(len(data)):
                table_form.append(
                    [
                        data[borrower]["username"],
                        data[borrower]["name"],
                        len(data[borrower]["loans"]),
                        data[borrower]["_id"]
                    ]
                )
            print(
                tabulate(
                    table_form,
                    headers = ["Username", "Name", "Outstanding Loans", "ID"],
                    tablefmt = "orgtbl"
                )
            )
            print("\nTo learn more about a borrower, copy their ID and")
            print("enter 'investigate user' and then inputting their ID.\n")
        elif item[0] == "exit":
            print("\nExiting search.\n")
            return None
        else:
            print("\nUnknown query.\n")

def user_investigate():
    global biblio
    global admin
    if not admin:
        print("\nYou must be logged in as an admin to use investigate.\n")
        return None
    id = input("\nInput ID of borrower |> ")
    try:
        oid = ObjectId(id)
    except Exception as e:
        print("\nInvalid ID detected.\n")
        return None
    data = biblio.get_borrower(oid)
    if data == None:
        print("\nNobody with given ID found.\n")
        return None
    print(
        tabulate(
            [
                [
                    data["username"],
                    data["name"],
                    data["phone"],
                    data["email"],
                    data["address"],
                    len(data["loans"]),
                    data["_id"]
                ]
            ],
            headers = [
                "Username",
                "Name",
                "Phone",
                "Email",
                "Address",
                "Outstanding",
                "ID"
            ],
            tablefmt = "orgtbl"
        )
    )

def user_delete():
    global biblio
    global borrower
    global borrower_data
    if type(borrower) != ObjectId:
        print("\nNot logged in yet.\n")
        return None
    confirm = input("Are you sure you want to delete your account? (y/n) |> ")
    if confirm != "y":
        print("\nAccount deletion aborted.\n")
        return None
    borrower_data = biblio.get_borrower(borrower)
    print("\nHere is the data about your account that will be deleted:\n")
    print(
        tabulate(
            [
                [
                    borrower_data["username"],
                    borrower_data["name"],
                    borrower_data["phone"],
                    borrower_data["email"],
                    borrower_data["address"]
                ]
            ],
            headers = ["Username", "Name", "Phone", "Email", "Address"],
            tablefmt = "orgtbl"
        )
    )
    biblio.delete_borrower(borrower)
    print("\nDeletion complete.\n")
    borrower = None
    borrower_data = None

def user_about():
    global biblio
    global borrower
    global borrower_data
    if type(borrower) != ObjectId:
        print("\nYou are not logged in yet.\n")
        return None
    borrower_data = biblio.get_borrower(borrower)
    print("\nHere is some data on you:\n")
    print(
        tabulate(
            [
                [
                    borrower_data["username"],
                    borrower_data["name"],
                    borrower_data["phone"],
                    borrower_data["email"],
                    borrower_data["address"],
                    len(borrower_data["loans"]),
                    borrower
                ]
            ],
            headers = [
                "Username",
                "Name",
                "Phone",
                "Email",
                "Address",
                "Outstanding",
                "ID"
            ],
            tablefmt = "orgtbl"
        )
    )

def user_loans():
    global biblio
    global borrower
    global borrower_data
    if type(borrower) != ObjectId:
        print("\nNot logged in.\n")
        return None
    borrower_data = biblio.get_borrower(borrower)
    loans = []
    for loan in borrower_data["loans"]:
        start = str(loan["begin_date"].year)+"/"+str(loan["begin_date"].month)+"/"+str(loan["begin_date"].day)
        end = str(loan["end_date"].year)+"/"+str(loan["end_date"].month)+"/"+str(loan["end_date"].day)
        loans.append(
            [
                biblio.get_book(loan["book"])["name"],
                start,
                end,
                loan["_id"]
            ]
        )
    print(
        tabulate(
            loans,
            headers = ["Book Name", "Start Date", "End Date", "Loan ID"],
            tablefmt = "orgtbl"
        )
    )
    print("\nTo return a book, enter 'return book', copy the Loan ID of the")
    print("book and then enter the Loan ID.\n")

def book_borrow():
    global biblio
    global borrower
    global borrower_data
    if type(borrower) != ObjectId:
        print("\nNot logged in yet.\n")
        return None
    book = input("Enter ID of book |> ")
    try:
        book_id = ObjectId(book)
    except Exception as e:
        print("\nErroneous book ID inputted.\n")
        return None
    borrower_data = biblio.get_borrower(borrower)
    if len(borrower_data["loans"]) >= biblio.get_meta()["quota"]:
        print("\nYou have maxed out your account.")
        print(f"Max books: {biblio.get_meta()['quota']}")
        return None
    if not biblio.book_exists(book_id):
        print("\nBook with ID given does not exist.\n")
        return None
    if biblio.get_book(book_id)["borrowed"]:
        print("\nBook is currently held by someone else. Come back later.\n")
        return None
    begin_date = datetime.utcnow()
    end_date = datetime.utcnow() + timedelta(days=biblio.get_meta()["period"])
    loan = biblio.add_loan(
        book = book_id,
        borrower = borrower,
        begin_date = begin_date,
        end_date = end_date
    )
    start = str(begin_date.year)+"/"+str(begin_date.month)+"/"+str(begin_date.day)
    end = str(end_date.year)+"/"+str(end_date.month)+"/"+str(end_date.day)
    print("\nLoan details:\n")
    print(
        tabulate(
            [
                [
                    biblio.get_book(book_id)["name"],
                    biblio.get_borrower(borrower)["username"],
                    start,
                    end
                ]
            ],
            headers = ["Book Name", "Borrower Username", "Start", "End"],
            tablefmt = "orgtbl"
        )
    )

def return_loan():
    global biblio
    global borrower
    global borrower_data
    if type(borrower) != ObjectId:
        print("\nNot logged in.\n")
        return None
    borrower_data = biblio.get_borrower(borrower)
    loans_id = [loan["_id"] for loan in borrower_data["loans"]]
    mort = input("Enter ID of loan to amortise |> ")
    try:
        mort_id = ObjectId(mort)
    except Exception as e:
        print("\nErroneous ID entered.\n")
        return None
    if mort_id not in loans_id:
        print("\nLoan with loan ID given not found.\n")
        return None
    details = biblio.return_loan(mort_id)
    print("\nLoan details:\n")
    start = str(details["begin_date"].year)+"/"+str(details["begin_date"].month)+"/"+str(details["begin_date"].day)
    end = str(details["end_date"].year)+"/"+str(details["end_date"].month)+"/"+str(details["end_date"].day)
    print(
        tabulate(
            [
                [
                    biblio.get_book(details["book"])["name"],
                    start,
                    end,
                    datetime.utcnow() > details["end_date"]
                ]
            ],
            headers = ["Book Name", "Start", "End", "Late?"],
            tablefmt = "orgtbl"
        )
    )
    print("\nThanks for returning the books back to the library.\n")

def book_search():
    global biblio
    global biblio
    terms = {}
    sort = {}
    querying = True
    while querying:
        print("\nAdd, edit or delete queries with this format:")
        print("[update/delete/search/exit] [title/author/isbn]\n")
        print("\nConfigure sorting with this format:")
        print("sort [title/author/isbn/pages] [-1/0/1]\n")
        item = input("|> ").split(" ")
        if item[0] == "sort" and len(item) == 3:
            try:
                item[2] = int(item[2])
            except Exception as e:
                print("\nSorting direction is not an integer.\n")
                return None
            if not -1 <= item[2] <= 1:
                print("\nSorting direction is not within -1 to 1.")
                return None
            if item[1] == "title":
                item[1] = "name"
            elif item[1] == "author":
                item[1] = "authors"
            projections = ["name","authors","isbn","pages"]
            if item[1] in projections:
                sort[item[1]] = item[2]
            continue
        if item[0] in ["title", "authors", "isbn"] and len(item) != 2:
            print("\nQuery command does not follow format.\n")
            continue
        if item[0] == "update":
            search_term = input("\nPlease enter search term |> ")
            if item[1] == "title":
                terms["name"] = [search_term]
            elif item[1] == "author":
                terms["authors"] = [search_term]
            elif item[1] == "isbn":
                terms["isbn"] = [search_term]
            else:
                print(f"\nUnrecognised query item: {item[1]}\n")
        elif item[0] == "delete":
            deleted = terms.pop(item[1], item[1])
            print(f"Deleted query item: {deleted}")
        elif item[0] == "search":
            arrange = []
            for key, value in sort.items():
                if value != 0:
                    arrange.append((key, value))
            data = biblio.search_books(arrange, **terms)
            print("\n")
            table_form = []
            for book in range(len(data)):
                authors = ""
                for author in data[book]["authors"]:
                    authors += author + ";"
                genres = ""
                for genre in data[book]["genres"]:
                    genres += genre + ";"
                publishers = ""
                for publisher in data[book]["publisher"]:
                    publishers += publisher + ";"
                table_form.append(
                    [
                        data[book]["name"],
                        data[book]["isbn"],
                        authors,
                        data[book]["pages"],
                        data[book]["borrowed"],
                        data[book]["_id"]
                    ]
                )
            print(
                tabulate(
                    table_form,
                    headers = [
                        "Name",
                        "ISBN",
                        "Authors",
                        "Pages",
                        "Borrowed",
                        "ID"
                    ],
                    tablefmt = "orgtbl"
                )
            )
            print("\nTo borrow a book, copy its ID and enter 'borrow book',")
            print("then enter the ID.\n")
        elif item[0] == "exit":
            print("\nExiting search.\n")
            return None
        else:
            print("\nUnknown query.\n")

def book_add():
    global biblio
    global admin
    if not admin:
        print("\nYou must be logged in as an admin to modify books.\n")
        return None
    print("\nInsert a new book. If you don't know a piece of information of")
    print("the book you can skip it.\n")
    print("\nHowever you must input the name of the book.\n")
    book_name = input("Name of book |> ")
    if book_name == "":
        print("\nBook name is missing.\n")
        return None
    book_isbn = input("Internation Standard Book Number |> ")
    book_authors = input("Input authors (separate with ';') |> ").split(";")
    book_genres = input("Input genres (separate with ';') |> ").split(";")
    book_date = input("Input publishing data (YYYY/MM/DD) |> ").split("/")
    book_publishers = input("Input publishers (separate with ';') |> ").split(
        ";"
    )
    book_pages = input("Input number of pages |> ")
    book_words = input("Input number of words |> ")
    if input("Confirm details? (y/n) |> ") != "y":
        print("Book not added.")
        return None
    pub_date = book_date
    if book_date == [""]:
        pub_date = None
    else:
        try:
            pub_date = datetime(
                int(book_date[0]),
                int(book_date[1]),
                int(book_date[2])
            )
        except Exception as e:
            print("\nErroneous input for date detected.\n")
            return None
    if book_pages != "":
        try:
            book_pages = int(book_pages)
        except Exception as e:
            print("\nPages is not an integer.\n")
            return None
    else:
        book_pages = None
    if book_words != "":
        try:
            book_words = int(book_words)
        except Exception as e:
            print("\nWords is not an integer.\n")
            return None
    else:
        book_words = None
    id = biblio.add_book(
        name = book_name,
        authors = book_authors,
        genres = book_genres,
        isbn = book_isbn,
        pages = book_pages,
        words = book_words,
        pub_date = pub_date,
        publisher = book_publishers
    )
    print(
        tabulate(
            [
                [
                    book_name,
                    book_authors,
                    book_isbn,
                    book_pages,
                    id
                ]
            ],
            headers = [
                "Name",
                "Authors",
                "ISBN",
                "Pages",
                "ID"
            ],
            tablefmt = "orgtbl"
        )
    )

def book_delete():
    global biblio
    global admin
    if not admin:
        print("\nYou must be logged in as admin to delete a book.\n")
        return None
    id = input("Input ID of book to be deleted |> ")
    try:
        book_id = ObjectId(id)
    except Exception as e:
        print("\nID inputted is invalid.\n")
        return None
    if not biblio.book_exists(book_id):
        print("\nBook does not exist.\n")
        return None
    if input("Are you sure you want to delete? (y/n) |> ") != "y":
        print("\nBook not deleted.\n")
        return None
    data = biblio.delete_book(book_id)
    authors = ""
    for author in data["authors"]:
        authors += author + ";"
    print("\nBook data:\n")
    print(
        tabulate(
            [
                [
                    data["name"],
                    authors,
                    data["isbn"],
                    data["pages"]
                ]
            ],
            headers = ["Name", "Authors", "ISBN", "Pages"],
            tablefmt = "orgtbl"
        )
    )

def book_update():
    global biblio
    global admin
    if not admin:
        print("\nYou must be logged in as admin to edit books.\n")
        return None
    id = input("Input ID of book |> ")
    try:
        book_id = ObjectId(id)
    except Exception as e:
        print("\nInvalid ID inputted.\n")
        return None
    if not biblio.book_exists(book_id):
        print("\nBook with ID given doesn't exist.\n")
        return None
    edit = True
    while edit:
        fields = ["title", "isbn", "authors", "pages"]
        print("\nSelect the integer of any field to edit or exit:")
        print("\t1: name,")
        print("\t2: isbn,")
        print("\t3: authors,")
        print("\t4: pages")
        print("\t5: exit")
        field = input("\n|> ")
        try:
            field = int(field)
        except Exception as e:
            print("\nYou did not enter an integer.\n")
            field = ""
            continue
        if field < 1 or field > 5:
            print("\nOption out of range. Try again.\n")
            continue
        if field == 5:
            edit = False
            continue
        location = fields[field-1]
        if location == "title":
            location = "name"
        value = input("\nValue |> ")
        if field == 3:
            value = value.split(";")
        if field == 4:
            try:
                value = int(value)
            except Exception as e:
                print("\nValue given is not an integer.\n")
                return None
        biblio.update_book(book_id, **{location: value})
        print(f"\n{fields[field-1]} edited to {value}.\n")
    print("\nEdit successful.\n")
    return None

def book_who():
    global biblio
    global admin
    if not admin:
        print("\nYou must be logged in as an admin to modify books.\n")
        return None
    id = input("Input ID of book |> ")
    try:
        book_id = ObjectId(id)
    except Exception as e:
        print("\nInvalid ID inputted.\n")
        return None
    if not biblio.book_exists(book_id):
        print("\nBook with ID given doesn't exist.\n")
        return None
    data = biblio.search_loans(book=book_id, returned=False)
    if len(data) > 0:
        borrowed = biblio.get_borrower(data[0]["borrower"])["username"]
        book = biblio.get_book(data[0]["book"])["name"]
        print(tabulate([[book,borrowed]],headers = ["Name of book","Username of borrower"],tablefmt = "orgtbl"))
    else:
        print("\nThis book is free to borrow.\n")

def assistant():
    global ASSISTANT
    print(ASSISTANT)


# MAP OF COMMANDS TO FUNCTIONS

funcmap = {
    "login admin": admin_login,
    "logout admin": admin_logout,
    "exit admin": admin_exit,
    "login": user_login,
    "logout": user_logout,
    "new user": user_create,
    "edit user": user_update,
    "search user": user_search,
    "investigate user": user_investigate,
    "delete self": user_delete,
    "about self": user_about,
    "check loans": user_loans,
    "borrow book": book_borrow,
    "return book": return_loan,
    "search books": book_search,
    "add book": book_add,
    "delete book": book_delete,
    "edit book": book_update,
    "who borrowed": book_who,
    "help": assistant,
}


# INTERPRETER

while run:
    command = input("\nEnter a command |> ").lower()
    print("\n")
    if command in list(funcmap.keys()):
        try:
            funcmap[command]()
        except Exception as e:
            #print(f"\nERROR: {e}\n")
            raise Exception(e)
    else:
        print("\nUnknown command given. Please try again.\n")

input("You have exited Bibliothekos. Press return to close window |> ")
