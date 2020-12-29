import datetime
import librarium

run = True

print("Thank you for using Bibliothekos, your personal pocket library manager.")
print("Please enter your management login details.")

biblio = librarium.Library()

login_type = input("USE ENV? (y/n) >>> ")
if login_type == "y":
    try:
        from env import *
    except Exception as e:
        print("env.py missing.")
        run = False
    else:
        try:
            biblio.connect(
                cluster = cluster,
                username = username,
                password = password
            )
        except Exception as e:
            print("Could not connect.")
            run = False
        else:
            print("Connection success.")
else:
    cluster = input("Cluster Name >>> ") # librarium-ipdc0
    username = input("Username >>> ")
    password = input("Password >>> ")
    try:
        biblio.connect(
            cluster = cluster,
            username = username,
            password = password
        )
    except Exception as e:
        print("Could not connect.")
        run = False
    else:
        print("Connection success.")

# COMMANDS

def setup_database(client):
    name = input("Name of database >>> ")
    client.connect_db(name, True)
    print("Successfully connected to database.")

def env_database(client):
    client.connect_db(database, True)
    print("Successfully connected to database.")

def setup_collections(client):
    books = input("Name of books collection >>> ")
    borrowers = input("Name of borrowers collection >>> ")
    loans = input("Name of loans collection >>> ")
    library = input("Name of library collection >>> ")
    client.connect_col(
        True,
        books = books,
        borrowers = borrowers,
        loans = loans,
        library = library
    )
    print("Successfully connected to collections.")

def env_collections(client):
    client.connect_col(
        True,
        books = books,
        borrowers = borrowers,
        loans = loans,
        library = library
    )
    print("Successfully connected to collections.")

def add_book(client):
    name = input("Name of book >>> ")
    if name == "":
        print("Name is missing.")
        return None
    isbn = input("International Standard Book Number >>> ")
    authors = input("Authors of book (split with ';') >>> ").split(";")
    genres = input("Genres of book (split with ';') >>> ").split(";")
    pages = input("Number of Pages >>> ")
    if pages == "":
        pages = None
    else:
        try:
            pages = int(pages)
        except Exception as e:
            print("A non-integer was inputted as pages.")
            return None
    words = input("Number of Words >>> ")
    if words == "":
        words = None
    else:
        try:
            words = int(words)
        except Exception as e:
            print("A non-integer was inputted as words.")
            return None
    pub_date = input("Date of Publication (YYYY/MM/DD) >>> ").split("/")
    if pub_date == "":
        pub_date == None
    else:
        try:
            pub_date = datetime.datetime(
                int(pub_date[0]),
                int(pub_date[1]),
                int(pub_date[2])
            )
        except Exception as e:
            print("Erroneous input for date detected.")
            return None
    publisher = input("Publishers of book (split with ';') >>> ").split(";")
    id = client.add_book(
        name = name,
        isbn = isbn,
        authors = authors,
        genres = genres,
        pages = pages,
        words = words,
        pub_date = pub_date,
        publisher = publisher
    )
    print(f"\nID of book: {id}")

# COMMAND SWITCH CASE


funcmap = {
    "setup database": setup_database,
    "env database": env_database,
    "setup collections": setup_collections,
    "env collections": env_collections,
    "add book": add_book,
    #"edit book": edit_book,
    #"import books": import_books,
    #"search books": search_books,
    #"delete book": delete_book
}

# SHELL

while run:
    print("\n")
    command = input(">>> ")
    if command == "exit":
        run = False
    elif command in funcmap.keys():
        try:
            funcmap[command](biblio)
        except Exception as e:
            print(f"Error: {e}")
    else:
        print(f"Unknown command detected: {command}")

x = input("Closing Bibliothekos. Press enter to continue >>> ")
biblio.disconnect()
