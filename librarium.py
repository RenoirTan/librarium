# Import Modules

import bson
import datetime
import dns
import json
import pathlib
import pymongo
import pprint
import re
import time

class Library:
    """
    A library class that acts as an intermediary between user and library data.

    Example
    -------

        >>> import librarium
        >>> client = librarium.Library()
        >>> print(client)
        librarium.Library(User = Username, Cluster = Cluster_Name) at hexid

    Attributes
    ----------
    _client : pymongo.MongoClient
        MongoDB connection client object

    _user : str
        Username of user used to login to MongoDB cluster

    _cluster : str
        Name of the cluster storing the library data

    _database : pymongo.Database
        MongoDB database used to store library data

    _books : pymongo.Collection
        MongoDB collection used to store book data

    _borrowers : pymongo.Collection
        MongoDB collection used to store borrower data

    _loans : pymongo.Collection
        MongoDB collection used to store loan data

    _library : pymongo.Collection
        MongoDB collection used to store library metadata
    """
    def __init__(self):
        self._client = None
        self._user = ""
        self._cluster = ""
        self._database = None
        self._books = None
        self._borrowers = None
        self._loans = None
        self._library = None

    def __str__(self):
        return f"librarium.Library(User={self._user}, Cluster={self._cluster}) at {hex(id(self))}"

    def __repr__(self):
        return f"librarium.Library(User={self._user}, Cluster={self._cluster}) at {hex(id(self))}"

    #def __del__(self):
    #    if type(self._client) == pymongo.MongoClient:
    #        self._client.close()

    # CONNECT #

    def connect(self, **kwargs):
        """
        Connect to library cluster.

        Example
        -------

            >>> client = librarium.Library().connect(
                username = "username",
                password = "password",
                cluster = "cluster-12345"
            )
            >>> print(client)
            librarium.Library(User = username, Cluster = cluster-12345) at hexid

        Parameters
        ----------
        **kwargs
            username : str
            password : str
            cluster : str
                Cluster name with 5 character suffix behind

        Raises
        ------
        ConnectionFailure
            If programme fails to connect to MongoDB database.

        KeyError
            If one of the keyword arguments is missing.

        TypeError
            If one of the keyword arguments is not a string.

        Returns
        -------
        self : librarium.Librarium
        """
        uri = "mongodb+srv://"
        uri += kwargs["username"]
        uri += ":"
        uri += kwargs["password"]
        uri += "@"
        uri += kwargs["cluster"]
        uri += ".mongodb.net/<dbname>?retryWrites=true&w=majority"
        client = pymongo.MongoClient(uri) # Use URI to connect to cluster
        self._user = kwargs["username"]
        self._cluster = kwargs["cluster"]
        self._client = client
        return self

    def connect_uri(self, uri):
        """
        Connect to library cluster with URI.

        Example
        -------

            >>> client = librarium.Library().connect_uri(
                "mongodb+srv://username:password@cluster-12345.mongodb.net/test?authSource=admin&replicaSet=librarium-shard-0&readPreference=primary&appname=MongoDB%20Compass&ssl=true"
            )

        Parameters
        ----------
        uri : str
            MongoDB Cluster Connection URI string

        Raises
        ------
        ConnectionFailure
            If programme fails to connect to MongoDB database.

        TypeError
            If one of the keyword arguments is not a string.

        Returns
        -------
        self : librarium.Library
        """
        client = pymongo.MongoClient(uri) # Use URI to connect to cluster
        self._user = kwargs["username"]
        self._cluster = kwargs["cluster"]
        self._client = client
        return self

    def connect_db(self, name, create=False):
        """
        Connects internal attributes to associated database.

        Example
        -------

            >>> client = librarium.Library().connect(
                username = "username",
                password = "password",
                cluster = "cluster-12345"
            ).connect_db(
                name = "library",
                create = True
            )
            >>> print(client)
            librarium.Library(User = username, Cluster = cluster-12345) at hexid

        Parameters
        ----------
        name : str
            Name of database storing information about the library

        create : bool
            If database without the name given does not exist, whether to create a database of that name

        Raises
        ------
        AttributeError
            If cluster not set up yet.

        ConnectionFailure
            If unable to connect.

        TypeError
            If keyword arguments given are not strings or not connected to cluster yet.

        ValueError
            If no database with the name given exists and create parameter not explicitly given as True.

        Returns
        -------
        client : librarium.Library
        """
        if type(name) != str:
            raise TypeError("name is not a string.")
        if (name not in self._client.list_database_names() and
            not create):
            raise ValueError(f"No database with the name {name} exists")
        db = self._client[name]
        self._database = db
        return self

    def connect_col(self, create=False, **kwargs):
        """
        Connects internal attributes to library collections.

        Example
        -------

            >>> client = librarium.Library().connect(
                username = "username",
                password = "password",
                cluster = "cluster-12345"
            ).connect_db(
                name = "library",
                create = True
            ).connect_col(
                create = True,
                books = "books",
                borrowers = "borrowers",
                loans = "loans",
                library = "library"
            )
            >>> print(client)
            librarium.Library(User = username, Cluster = cluster-12345) at hexid

        Parameters
        ----------
        create : bool
            Whether to create a new collection if collection with specified name does not exist.

        **kwargs
            books : str
            borrowers : str
            loans : str
            library : str

        Raises
        ------
        AttributeError
            If database not setup yet.

        ConnectionFailure
            If could not connect to cluster.

        TypeError
            If keyword arguments given are not strings or booleans where required or not connected to cluster yet.

        ValueError
            If no collection with the names given exists and create parameter not explicitly given as True.

        Returns
        -------
        self : librarium.Library
        """
        collections = [
            "_books",
            "_borrowers",
            "_loans",
            "_library"
        ]
        for cols, name in kwargs.items():
            if type(name) != str:
                raise TypeError(
                    f"{cols} collection has a non-string name {name}"
                )
            if (name not in self._database.list_collection_names() and
                not create):
                raise ValueError(f"Collection with name {name} not found")
            ucols = "_" + cols
            if ucols in collections:
                setattr(
                    self,
                    ucols,
                    self._database[name]
                )
        return self

    def disconnect(self):
        """
        Disconnects from client.

        Example
        -------

            >>> client.disconnect()
        """
        if type(self._client) == pymongo.MongoClient:
            self._client.close()

    # BOOKS #

    def get_book(self, objectid):
        """
        Get details of borrower with just objectid

        Example
        -------

            >>> details = client.get_book(
                bson.objectid.ObjectId("507f191e810c19729de860ea")
            )

        Parameters
        ----------
        objectid : bson.objectid.ObjectId
            BSON ObjectId of book

        Raises
        ------
        TypeError
            If objectid is not a BSON ObjectId

        Returns
        -------
        details : None or dict
            Details of the book. None if book not found
        """
        if type(objectid) != bson.objectid.ObjectId:
            raise TypeError(f"objectid is not a BSON ObjectId: {objectid}")
        details = self._books.find_one({"_id": objectid})
        details["borrowed"] = self.book_borrowed(objectid)
        return details

    def find_books(self, name, exact=True, insensitive=False):
        """
        Find book(s) with name.

        Example
        -------

        >>> client.book_exists(
            name = "Romance of the Three Kingdoms"
        )
        True

        Parameters
        ----------
        name : str
            Name of the book

        within : bool
            Whether to search exact name or as regular expression

        insensitive : bool
            Case insensitivity

        Raises
        ------
        AttributiveError
            If book collection not connected yet

        TypeError
            If name is not a string or capital is not a boolean

        Returns
        -------
        book_ids : list of bson.objectid.ObjectId
            ObjectIds of books with the requested name
        """
        if type(name) != str:
            raise TypeError(f"name is not a string: {name}")
        term = name
        query = {"name": {"$regex": None, "$options": ""}}
        if exact:
            term = "^" + name
        query["name"]["$regex"] = term
        if insensitive:
            query["name"]["$options"] += "i"
        books = list(self._books.find(query))
        book_ids = [x["_id"] for x in books]
        return book_ids

    def book_exists(self, objectid):
        """
        Check if book exists with ObjectId.

        Example
        -------

            >>> client.book_exists(
                bson.objectid.ObjectId(
                    "5f019ed2ffd6b60fae41212f"
                )
            )

        Parameters
        ----------
        objectid : bson.objectid.ObjectId or None
            Book objectid

        Raises
        ------
        TypeError
            If objectid is not a BSON ObjectId

        Returns
        -------
        exists : bool
            Whether book exists
        """
        if objectid == [] or objectid == None:
            return False
        if type(objectid) != bson.objectid.ObjectId:
            raise TypeError("objectid is not a BSON ObjectId")
        book = self._books.find_one(
            {"_id": objectid}
        )
        return book != None

    def book_borrowed(self, book):
        """
        Check whether a book is borrowed

        Example
        -------

            >>> client.book_borrowed(ObjectId("5f093da5a893e6381d402bb4"))
            True

        Parameters
        ----------
        book : bson.objectid.ObjectId
            BSON ObjectId of Book

        Raises
        ------
        TypeError
            If book is not a BSON ObjectId
        """
        if type(book) != bson.objectid.ObjectId:
            raise TypeError(f"book is not a BSON ObjectId: {book}")
        loans = list(self._loans.find({"book": book, "returned": False}))
        return loans != []

    def add_book(self, name, **kwargs):
        """
        Add a book into collection.

        Notes

        Example
        -------

            >>> id = client.add_book(
                name = "Trump: The Art of the Deal",
                authors = [
                    "Donald John Trump",
                    "Tony Schwartz"
                ],
                isbn = "0-394-55528-7",
                genres = [
                    "Business"
                ]
                pages = 372
                words = 86855
                pub_date = {
                    "year": 1987,
                    "month": 11,
                    "day": 1
                },
                publisher = "Random House"
            )
            >>> print(id)
            ObjectId('...')

        Parameters
        ----------
        name : str
            Name of the book

        **kwargs : dict
            authors : str or list of str
                Author name or list of authors' names
            genres : str or list of str
                Genre of the book
            isbn : str
                International standard book number of the book
            pages : int
                Number of pages
            words : int
                Number of words
            pub_date : datetime.datetime or dict of int
                Date of the book's writing or dictionary of year, month and day
            publisher : str or list of str
                Name or names of publishers

        Raises
        ------
        AttributeError
            If book collection not connected to yet

        KeyError
            If mandatory keys are missing

        TypeError
            If any of the parameters given are not correct in their data type or name is missing

        ValueError
            If erroneous date inputted

        Returns
        -------
        book.inserted_id : bson.objectid.ObjectId
            ObjectId of the book added to the collection
        """
        kwkeys = list(kwargs.keys()) # Return list to reduce processing time
        document = {
            "name": None,
            "authors": [],
            "isbn": None,
            "genres": [],
            "pages": None,
            "words": None,
            "pub_date": None,
            "publisher": []
        }
        if type(name) != str:
            raise TypeError(f"name is not a string: {name}")
        document["name"] = name
        list_of_str = ["authors", "genres", "publisher"]
        for item in list_of_str:
            if item not in kwkeys:
                continue
            if kwargs[item] == None:
                continue
            if type(kwargs[item]) == list:
                for entity in kwargs[item]:
                    document[item].append(
                        str(entity)
                    )
            else:
                document[item].append(
                    str(kwargs[item])
                )
        string = ["isbn"]
        for item in string:
            if item not in kwkeys:
                continue
            if kwargs[item] == None:
                continue
            document[item] = str(kwargs[item])
        integer = ["pages", "words"]
        for item in integer:
            if item not in kwkeys:
                continue
            if kwargs[item] == None:
                continue
            document[item] = int(kwargs[item])
        date_and_time = ["pub_date"]
        for item in date_and_time:
            if item not in kwkeys:
                continue
            if kwargs[item] == None:
                continue
            if type(kwargs[item]) == datetime.datetime:
                document[item] = kwargs[item]
            elif type(kwargs[item]) == dict:
                document[item] = datetime.datetime(
                    year = kwargs[item]["year"],
                    month = kwargs[item]["month"],
                    day = kwargs[item]["day"]
                )
            else:
                raise TypeError(
                    f"{item} is not datetime.datetime or dictionary"
                )
        document["last_updated"] = datetime.datetime.utcnow()
        book = self._books.insert_one(document)
        return book.inserted_id

    def update_book(self, objectid, **kwargs):
        """
        Update a book in the collection

        Example
        -------

            >>> id = client.add_book(
                name = "Trump: The Art of the Deal",
                authors = [
                    "Donald John Trump",
                    "Tony Schwartz"
                ],
                isbn = "0-394-55528-7",
                genres = [
                    "Business"
                ]
                pages = 372
                words = 86855
                pub_date = {
                    "year": 1969, # Erroneous data
                    "month": 11,
                    "day": 1
                },
                publisher = "Random House"
            )
            >>> client.update_book(
                objectid = id
                pub_date = {
                    "year": 1987,
                    "month": 11,
                    "day": 1
                }
            )

        Parameters
        ----------
        objectid : bson.objectid.ObjectId
            ObjectId of wanted book

        **kwargs : dict
            name : str
                Name of the book
            authors : str or list of str
                Author name or list of authors' names
            isbn : str
                International standard book number of the book
            genres : str or list of str
                Genres of the book
            pages : int
                Number of pages
            words : int
                Number of words
            pub_date : datetime.datetime or dict of int
                Date of the book's writing or dictionary of year, month and day
            publisher : str or list of str
                Name or names of publishers
        """
        kwkeys = list(kwargs.keys())
        if not self.book_exists(objectid):
            raise ValueError(
                f"Book with requested ObjectId does not exist: {objectid}"
            )
        document = {}
        list_of_str = ["authors", "genres", "publisher"]
        for item in list_of_str:
            if item not in kwkeys:
                continue
            if kwargs[item] == None:
                continue
            if type(kwargs[item]) == list:
                for entity in kwargs[item]:
                    document[item].append(
                        str(entity)
                    )
            else:
                document[item].append(
                    str(kwargs[item])
                )
        string = ["name", "isbn"]
        for item in string:
            if item not in kwkeys:
                continue
            if kwargs[item] == None:
                continue
            document[item] = str(kwargs[item])
        integer = ["pages", "words"]
        for item in integer:
            if item not in kwkeys:
                continue
            if kwargs[item] == None:
                continue
            document[item] = int(kwargs[item])
        date_and_time = ["pub_date"]
        for item in date_and_time:
            if item not in kwkeys:
                continue
            if kwargs[item] == None:
                continue
            if type(kwargs[item]) == datetime.datetime:
                document[item] = kwargs[item]
            elif type(kwargs[item]) == dict:
                document[item] = datetime.datetime(
                    year = kwargs[item]["year"],
                    month = kwargs[item]["month"],
                    day = kwargs[item]["day"]
                )
            else:
                raise TypeError(
                    f"{item} is not datetime.datetime or dictionary"
                )
        document["last_updated"] = datetime.datetime.utcnow()
        self._books.update_one(
            {"_id": objectid},
            {"$set": document}
        )

    def add_books(self, books):
        """
        Add multiple books to collection.

        Example
        -------

            >>> books = [
                {
                    name = "Trump: The Art of the Deal",
                    authors = [
                        "Donald John Trump",
                        "Tony Schwartz"
                    ],
                    isbn = "0-394-55528-7",
                    genres = [
                        "Business"
                    ]
                    pages = 372
                    words = 86855
                    pub_date = {
                        "year": 1987,
                        "month": 11,
                        "day": 1
                    },
                    publisher = "Random House"
                },
                {
                    name = "A Pickle for the Knowing Ones",
                    authors = [
                        "Timothy Dexter"
                    ],
                    isbn = "978-0-344-45584-1",
                    genres = [
                        "Politics"
                    ]
                    pages = 37
                    words = None
                    pub_date = {
                        "year": 1797,
                        "month": 1,
                        "day": 22
                    },
                    publisher = "Random House"
                }
            ]
            >>> print(books)
            [ObjectId('...'),ObjectId('...')]

        Parameters
        ----------
        books : list of dict of str, int, datetime.datetime, list of str or dict of int
            List of books with parameters to be inputted into the system. Parameters should match the **kwargs format in librarium.Library.add_books

        Raises
        ------
        AttributeError
            If book collection not connected to yet

        KeyError
            If mandatory keys are missing

        TypeError
            If any of the parameters given are not correct in their data type or name is missing

        ValueError
            If erroneous date inputted

        Returns
        -------
        book_ids : list of bson.objectid.ObjectId
            List of ObjectIds of the books added to the library.
        """
        return [self.add_book(**book) for book in books]

    def import_books(self, filepath):
        """
        Import books from a JSON or BSON file.

        Notes
        -----
        The JSON and BSON file should have an array as the first-level data.

        Example
        -------

            >>> books = client.import_books(
                filepath = pathlib.Path("books.json")
            )

        Parameters
        ----------
        filepath : str or pathlib.Path
            File path in string or pathlib.Path form (recommended)

        Raises
        ------
        FileNotFoundError
            File with the requested name through the requested path not found

        TypeError
            If filepath is not a string or pathlib.Path

        ValueError
            If file is not a JSON or BSON file

        Returns
        -------
        books_id : list of bson.objectid.ObjectId
        """
        decoder = ""
        file = None
        if type(filepath) == str:
            if filepath.endswith(".json"):
                decoder = "JSON"
            elif filepath.endswith(".bson"):
                decoder = "BSON"
            else:
                raise ValueError("file is not a JSON or BSON file")
        elif type(filepath) == pathlib.Path:
            if filepath.suffix == ".json":
                decoder = "JSON"
            elif filepath.suffix == ".bson":
                decoder = "BSON"
            else:
                raise ValueError("file is not a JSON or BSON file")
        else:
            raise TypeError("filepath is not a string or pathlib.Path")
        if decoder == "JSON":
            data = json.load(open(filepath, "r"))
        elif decoder == "BSON":
            data = bson.loads(open(filepath,"r").read())
        return self.add_books(data)

    def search_books(self, sort=[], **terms):
        """
        Search books based on different available queries.

        Example
        -------

            >>> info = client.search_books(
                sort = [("isbn",1)],
                name = ["Trump: The Art of"],
                authors = ["Donald John", "Timot"],
                isbn = ["0-394"],
                genres = ["Business"],
                pages = [{"$gte": 370, "$lte": 375}]
                words = [{"$gte": 80000, "$lte": 90000}],
                pub_date = [
                    {
                        "$lte": datetime.datetime(1988,1,1),
                        "$gte": datetime.datetime(1986,1,1)
                    }
                ]
                publisher = ["Random House"],
            )
            >>> print(info)
            [{data}]

        Parameters
        ----------
        sort : list of tuple of str, int
            How to sort returned items

        **terms : dict
            name : list of str
            authors : list of str
            isbn : list of str
            genres : list of str
            pages : list of dict of int
            words : list of dict of int
            pub_date : list of dict of datetime.datetime
            publisher : list of str

        Raises
        ------
        AttributeError
            If book collection not connected to yet

        KeyError
            If mandatory keys are missing

        TypeError
            If any of the parameters given are not correct in their data type or **terms is missing

        ValueError
            If erroneous date inputted

        Returns
        -------
        list of dict
        """
        trmkeys = list(terms.keys())
        and_string = ["name", "isbn", "authors", "genres", "publisher"]
        or_int = ["pages", "words", "pub_date"]
        query = {"$and": []}
        for item in and_string:
            inner_query = {"$and": []}
            if item not in trmkeys:
                continue
            if terms[item] == None:
                continue
            for term in terms[item]:
                if term != "":
                    inner_query["$and"].append(
                        {item: {"$regex": term, "$options": "i"}}
                    )
            if inner_query != {"$and": []}:
                query["$and"].append(inner_query)
        for item in or_int:
            inner_query = {"$or": []}
            if item not in trmkeys:
                continue
            if terms[item] == None:
                continue
            for term in terms[item]:
                if term != {}:
                    inner_query["$or"].append({item: term})
            if inner_query == {"$or": []}:
                query["$and"].append(inner_query)
        if query == {"$and": []}:
            query = {}
        if sort == []:
            books = list(self._books.find(query))
        else:
            books = list(self._books.find(query).sort(sort))
        for book in range(len(books)):
            books[book]["borrowed"] = self.book_borrowed(books[book]["_id"])
        return books

    def delete_book(self, objectid):
        """
        Delete a book with a matching objectid

        Example
        -------

            >>> book_id = client.find_books(
                name = "Trump",
                exact = False,
                insensitive = False
            )[0]
            >>> client.delete_book(book_id)

        Parameters
        ----------
        objectid : bson.objectid.ObjectId
            BSON ObjectId of book

        Raises
        ------
        TypeError
            objectid is not a BSON ObjectId

        Returns
        -------
        info : None or dict
            Info about deleted book or None if book not found
        """
        if type(objectid) != bson.objectid.ObjectId:
            raise TypeError(f"objectid is not a BSON ObjectId: {objectid}")
        return self._books.find_one_and_delete({"_id": objectid})

    # BORROWERS #

    def get_borrower(self, objectid):
        """
        Get details of borrower with just objectid

        Example
        -------

            >>> details = client.get_borrower(
                bson.objectid.ObjectId("507f191e810c19729de860ea")
            )

        Parameters
        ----------
        objectid : bson.objectid.ObjectId
            BSON ObjectId of borrower

        Raises
        ------
        TypeError
            If objectid is not a BSON ObjectId

        Returns
        -------
        details : None or dict
            Details of the borrower. None if borrower not found
        """
        if type(objectid) != bson.objectid.ObjectId:
            raise TypeError(f"objectid is not a BSON ObjectId: {objectid}")
        details = self._borrowers.find_one({"_id": objectid})
        details["loans"] = self.search_loans(
            borrower = objectid,
            returned = False
        )
        return details

    def find_borrowers(self, username, exact=True, insensitive=False):
        """
        Find borrower(s) with username.

        Example
        -------

        >>> client.find_borrower(
            username = "timmytom"
        )
        ObjectId(...)

        Parameters
        ----------
        username : str
            Username of the borrower

        exact : bool
            Whether to search exact name or as regular expression

        insensitive : bool
            Case insensitivity

        Raises
        ------
        AttributiveError
            If borrower collection not connected yet

        TypeError
            If name is not a string or capital is not a boolean

        Returns
        -------
        borrower_ids : list of bson.objectid.ObjectId
            ObjectIds of borrowers with the requested name
        """
        if type(username) != str:
            raise TypeError(f"username is not a string: {name}")
        term = username
        query = {"username": {"$regex": None, "$options": ""}}
        if exact:
            term = "^" + username
        query["username"]["$regex"] = term
        if insensitive:
            query["username"]["$options"] += "i"
        borrowers = list(self._borrowers.find(query))
        borrower_ids = [x["_id"] for x in borrowers]
        return borrower_ids

    def borrower_exists(self, objectid):
        """
        Check if borrower exists with ObjectId.

        Example
        -------

            >>> client.borrower_exists(
                bson.objectid.ObjectId(
                    "5f019ed2ffd6b60fae41212f"
                )
            )

        Parameters
        ----------
        objectid : bson.objectid.ObjectId or None
            Borrower objectid

        Raises
        ------
        TypeError
            If objectid is not a BSON ObjectId

        Returns
        -------
        exists : bool
            Whether borrower exists
        """
        if objectid == [] or objectid == None:
            return False
        if type(objectid) != bson.objectid.ObjectId:
            raise TypeError("objectid is not a BSON ObjectId")
        borrower = self._borrowers.find_one(
            {"_id": objectid}
        )
        return borrower != None

    def add_borrower(self, username, password, name, phone, email, address):
        """
        Add a borrower into collection.

        Notes

        Example
        -------

            >>> id = client.add_borrower(
                username = "timtam-chocolates",
                password = "youwontguessthisxd",
                name = "Tim Tom",
                phone = "999"
                email = "fake_email@liame.com",
                address = "123 Tuas Link S147258",
                skip = False
            )
            >>> print(id)
            ObjectId('...')

        Parameters
        ----------
        username : str
            Username of the borrower

        password : str
            Password used to

        name : str
            Real life name of the borrower

        phone : str
            Phone number of borrower. Can have separation marks

        email : str
            Email of the borrower

        address : str
            Home address of the borrower

        Raises
        ------
        AttributeError
            If borrower collection not connected to yet

        TypeError
            If any of the parameters given are not correct in their data type

        ValueError
            If borrower with the same username found

        Returns
        -------
        borrower.inserted_id : bson.objectid.ObjectId
            ObjectId of the borrower added to the collection
        """
        found = self.find_borrowers(username,True,False)
        if found != []:
            raise ValueError(
                f"borrower with the same username found: {username}"
            )
        if type(username) != str:
            raise TypeError("username is not a string")
        if type(password) != str:
            raise TypeError("password is not a string")
        if type(name) != str:
            raise TypeError("name is not a string")
        if type(phone) != str:
            raise TypeError("phone is not a string")
        if type(email) != str:
            raise TypeError("email is not a string")
        if type(address) != str:
            raise TypeError("address is not a string")
        document = {
            "username": username,
            "password": password,
            "name": name,
            "phone": phone,
            "email": email,
            "address": address,
            "last_updated": datetime.datetime.utcnow()
        }
        return self._borrowers.insert_one(document).inserted_id

    def update_borrower(self, objectid, **kwargs):
        """
        Update a borrower in the collection

        Example
        -------

            >>> id = client.add_borrower(
                username = "yamai",
                password = "password",
                name = "Josg Michael Tmg",
                phone = "999",
                address = "123 Tuas Link S147258"
                email = "creative.name@coolmail.biz.su"
            )
            >>> client.update_borrower(
                objectid = id,
                name = "Josh Michael Tng"
            )

        Parameters
        ----------
        objectid : bson.objectid.ObjectId
            ObjectId of wanted borrower

        **kwargs : dict
            password : str
                Password used to
            name : str
                Real life name of the borrower
            phone : str
                Phone number of the borrower
            email : str
                Email of the borrower
            address : str
                Home address of the borrower

        Raises
        ------
        TypeError
            If type of kwargs parameters are not the correct type

        ValueError
            If email is not a valid email
        """
        if type(objectid) != bson.objectid.ObjectId:
            raise TypeError("objectid is not a BSON ObjectId")
        keywords = [
            "password",
            "name",
            "phone",
            "email",
            "address"
        ]
        document = {}
        for key, value in kwargs.items():
            if key not in keywords:
                continue
            if type(value) != str:
                raise TypeError(
                    f"{value} associated with {key} is not a string"
                )
            document[key] = value
        document["last_updated"] = datetime.datetime.utcnow()
        self._borrowers.update_one(
            {"_id": objectid},
            {"$set": document}
        )

    def add_borrowers(self, borrowers, update=False):
        """
        Add multiple books to collection.

        Example
        -------

            >>> borrowers = [
                {
                    username = "timtam-chocolates",
                    password = "youwontguessthisxd",
                    name = "Tim Tom",
                    phone = "999",
                    email = "fake_email@liame.com",
                    address = "123 Tuas Link S147258"
                },
                {
                    username = "yamai",
                    password = "password",
                    name = "Josh Michael Tng",
                    phone = "743978932",
                    address = "123 Tuas Link S147258"
                    email = "creative.name@coolmail.biz"
                }
            ]
            >>> print(borrowers, update=False)
            [ObjectId('...'),ObjectId('...')]

        Parameters
        ----------
        borrowers : list of dict of str
            List of borrowers with parameters to be inputted into the system. Available parameters are listed in self.add_borrower()

        update : bool
            Whether to update if the borrower with the same username is found

        Raises
        ------
        AttributeError
            If borrower collection not connected to yet

        KeyError
            If mandatory keys are missing

        TypeError
            If any of the parameters given are not correct in their data type or name is missing

        ValueError
            If erroneous date inputted

        Returns
        -------
        borrower_ids : list of bson.objectid.ObjectId
            List of ObjectIds of the borrowers added to the library.
        """
        if not update:
            return [self.add_borrower(**borrower) for borrower in borrowers]
        borrower_ids = []
        for borrower in borrowers:
            found = self.find_borrowers(borrower["username"], True, False)
            if found == []:
                borrower_ids.append(
                    self.add_borrower(
                        **borrower
                    )
                )
            else:
                self.update_borrower(
                    objectid = found[0],
                    **borrower
                )
                borrower_ids.append(found[0])
        return borrower_ids

    def import_borrowers(self, filepath, update=False):
        """
        Import borrowers from a JSON or BSON file.

        Notes
        -----
        The JSON and BSON file should have an array as the first-level data.

        Example
        -------

            >>> borrowers = client.import_borrowers(
                filepath = pathlib.Path("borrowers.json"),
                update = True
            )

        Parameters
        ----------
        filepath : str or pathlib.Path
            File path in string or pathlib.Path form (recommended)

        update : bool
            Whether to update if the borrower if a borrower with the same name is found

        Raises
        ------
        FileNotFoundError
            File with the requested name through the requested path not found

        TypeError
            If filepath is not a string or pathlib.Path

        ValueError
            If file is not a JSON or BSON file

        Returns
        -------
        borrowers_id : list of bson.objectid.ObjectId
        """
        decoder = ""
        file = None
        if type(filepath) == str:
            if filepath.endswith(".json"):
                decoder = "JSON"
            elif filepath.endswith(".bson"):
                decoder = "BSON"
            else:
                raise ValueError("file is not a JSON or BSON file")
        elif type(filepath) == pathlib.Path:
            if filepath.suffix == ".json":
                decoder = "JSON"
            elif filepath.suffix == ".bson":
                decoder = "BSON"
            else:
                raise ValueError("file is not a JSON or BSON file")
        else:
            raise TypeError("filepath is not a string or pathlib.Path")
        if decoder == "JSON":
            data = json.load(open(filepath, "r"))
        elif decoder == "BSON":
            data = bson.loads(open(filepath,"r").read())
        return self.add_borrowers(data, update=update)

    def search_borrowers(self, sort=[], **terms):
        """
        Search books based on different available queries.

        Example
        -------

            >>> info = client.search_books(
                name = ["Josh"]
            )
            >>> print(info)
            [{data}]

        Parameters
        ----------
        sort : list of tuple, int
            How to sort items

        **terms : dict
            username : list of str
            password : list of str
            name : list of str
            phone : list of str
            email : list of str
            address : list of str

        Raises
        ------
        AttributeError
            If borrower collection not connected to yet

        KeyError
            If mandatory keys are missing

        TypeError
            If any of the parameters given are not correct in their data type or **terms is missing

        ValueError
            If erroneous date inputted

        Returns
        -------
        list of dict
        """
        trmkeys = list(terms.keys())
        and_string = [
            "username",
            "password",
            "name",
            "phone",
            "email",
            "address"
        ]
        query = {"$and": []}
        for item in and_string:
            inner_query = {"$and": []}
            if item not in trmkeys:
                continue
            if terms[item] == None:
                continue
            for term in terms[item]:
                if term != "":
                    inner_query["$and"].append(
                        {item: {"$regex": term, "$options": "i"}}
                    )
            if inner_query != {"$and": []}:
                query["$and"].append(inner_query)
        if query == {"$and": []}:
            query = {}
        if sort == []:
            borrowers = list(self._borrowers.find(query))
        else:
            borrowers = list(self._borrowers.find(query).sort(sort))
        for borrower in range(len(borrowers)):
            borrowers[borrower]["loans"] = self.search_loans(
                borrower = borrowers[borrower]["_id"],
                returned = False
            )
        return borrowers

    def delete_borrower(self, objectid):
        """
        Delete a borrower with a matching objectid

        Example
        -------

            >>> client.delete_book(book_id)

        Parameters
        ----------
        objectid : bson.objectid.ObjectId
            BSON ObjectId of borrower

        Raises
        ------
        TypeError
            objectid is not a BSON ObjectId

        Returns
        -------
        info : None or dict
            Info about deleted borrower or None if borrower not found
        """
        if type(objectid) != bson.objectid.ObjectId:
            raise TypeError(f"objectid is not a BSON ObjectId: {objectid}")
        return self._borrowers.find_one_and_delete({"_id": objectid})

    # LOANS #

    def add_loan(self, book, borrower, begin_date, end_date):
        """
        Check out a book

        Example
        -------

            >>> loan = client.add_loan(
                book = ObjectId("5f0346e5dc308a044f7d4baf"),
                borrower = ObjectId("5f093da5a893e6381d402bb4"),
                begin_date = datetime.datetime.utcnow(),
                end_date = datetime.datetime.utcnow() + datetime.timedelta(day=7)
            )
            >>> print(loan)
            ObjectId('...')

        Parameters
        ----------
        book : bson.objectid.ObjectId
            BSON ObjectId of book

        borrower : bson.objectid.ObjectId
            BSON ObjectId of borrower

        begin_date : datetime.datetime or dict of int
            Date and time of borrowing

        end_date : datetime.datetime or dict of int
            Date and time of end of loan

        Raises
        ------
        TypeError
            If data type of each parameter is not correct

        ValueError
            If book or borrower does not exist

        Return
        ------
        None or bson.objectid.ObjectId
            BSON ObjectId of loan, or None if book had not been returned yet
        """
        if type(book) != bson.objectid.ObjectId:
            raise TypeError(f"book is not a BSON ObjectId: {book}")
        if self.book_borrowed(book):
            return None
        if not self.book_exists(book):
            raise ValueError(f"book does not exist")
        if type(borrower) != bson.objectid.ObjectId:
            raise TypeError(f"book is not a BSON ObjectId: {borrower}")
        if not self.borrower_exists(borrower):
            raise ValueError(f"borrower does not exist")
        if type(begin_date) == dict:
            start = {}
            start = datetime.datetime(
                year = begin_date["year"],
                month = begin_date["month"],
                day = begin_date["day"]
            )
        elif type(begin_date) == datetime.datetime:
            start = begin_date
        else:
            raise TypeError(
                f"start is not a datetime.datetime nor a dictionary representing a date: {begin_date}"
            )
        if type(end_date) == dict:
            end = {}
            end = datetime.datetime(
                year = end_date["year"],
                month = end_date["month"],
                day = end_date["day"]
            )
        elif type(end_date) == datetime.datetime:
            end = end_date
        else:
            raise TypeError(
                f"end is not a datetime.datetime nor a dictionary representing a date: {end_date}"
            )
        document = {
            "book": book,
            "borrower": borrower,
            "begin_date": start,
            "end_date": end,
            "returned": False
        }
        return self._loans.insert_one(document).inserted_id

    def search_loans(self, sort=[], **terms):
        """
        Search loans with terms.

        Example
        -------

            >>> info = client.search_loans(
                sort = [("end_date", -1)]
                end_date = {"$gte": datetime.datetime(2019,12,31)}
            )
            >>> print(info)
            [{data}]

        Parameters
        ----------
        sort : list of tuple of str, int

        **terms : dict
            book : bson.objectid.ObjectId
            borrower : bson.objectid.ObjectId
            begin_date : dict of str, datetime.datetime
            end_date : dict of str, datetime.datetime
            returned : bool

        Raises
        ------
        AttributeError
            If borrower collection not connected to yet

        KeyError
            If mandatory keys are missing

        TypeError
            If any of the parameters given are not correct in their data type or **terms is missing

        ValueError
            If erroneous date inputted

        Returns
        -------
        list of dict
        """
        trmkeys = list(terms.keys())
        and_items = ["book", "borrower", "begin_date", "end_date", "returned"]
        query = {"$and": []}
        for item in and_items:
            if item not in trmkeys:
                continue
            if terms[item] == None:
                continue
            if terms[item] != "" and terms[item] != {}:
                query["$and"].append({item: terms[item]})
        if query == {"$and": []}:
            query = {}
        if sort == []:
            return list(self._loans.find(query))
        else:
            return list(self._loans.find(query).sort(sort))

    def return_loan(self, objectid):
        """
        Return a book with objectid of loan

        Example
        -------

            >>> details = client.return_loan(
                ObjectId("5f09ca2e3ff8003648357482")
            )
            >>> print(details)
            {data}

        Parameters
        ----------
        objectid : bson.objectid.ObjectId
            BSON ObjectId of loan

        Raises
        ------
        TypeError
            If objectid is not a BSON ObjectId

        ValueError
            If loan does not exist

        Returns
        -------
        details : dict
            Dictionary of details of loan
        """
        if type(objectid) != bson.objectid.ObjectId:
            raise TypeError(f"objectid is not a BSON ObjectId: {objectid}")
        loan = self._loans.find_one({"_id": objectid})
        if loan == None:
            raise ValueError(f"loan with objectid not found: {objectid}")
        self._loans.update_one(
            {"_id": objectid},
            {"$set":{"returned": True}}
        )
        details = self._loans.find_one({"_id": objectid})
        details["late"] = (datetime.datetime.utcnow() > details["end_date"])
        return details

    # LIBRARY METADATA

    def get_meta(self):
        """
        Get metadata about library. Metadata includes maximum items borrowable (quota) and days per book allowed (period)

        Example
        -------

            >>> print(client.get_meta())
            {"quota": 16, "period": 14}

        Raises
        ------
        AttributeError
            If library collection not connected yet

        Returns
        -------
        dict
        """
        return self._library.find_one({})
