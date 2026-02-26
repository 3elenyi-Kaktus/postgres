# PostgreSQL database connector

### _by 3elenyi Kaktus_

Holds base connector class to operate on PostgreSQL databases.

## Internal logic
A base class should not be used directly. A proper realization is inheriting a custom class from `DBConnector` and adding all needed methods to it. All undercover interactions with DB must be done via the base class though. To create a new instance of a class the `DBConnector.create()` method must be used. It is designed to work correctly in inherited classes.

As return format of every SQL query is a list of tuples by default, it is advised to use a custom factory class to create a predictable data holders. To do so, a simple dataclass should be created, implementing all the column names of a selected table, inheriting from internal Factory class. Then this class schema can be used when executing SQL queries.

If the query is a non-fetchable one, it must be stated so.