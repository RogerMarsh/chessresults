# __init__.py
# Copyright 2008 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Chess results database."""
from solentware_base.core.constants import (
    BERKELEYDB_MODULE,
    BSDDB3_MODULE,
    DPT_MODULE,
    SQLITE3_MODULE,
    APSW_MODULE,
    UNQLITE_MODULE,
    VEDIS_MODULE,
    DB_TCL_MODULE,
    LMDB_MODULE,
)

# berkeleydb interface module name
_BERKELEYDBRESULTS = __name__ + ".berkeleydb.resultsdatabase"

# bsddb3 interface module name
_DBRESULTS = __name__ + ".db.resultsdatabase"

# DPT interface module name
_DPTRESULTS = __name__ + ".dpt.resultsdatabase"

# Sqlite3 interface module name
_SQLITE3RESULTS = __name__ + ".sqlite.resultsdatabase"

# apsw interface module name
_APSWRESULTS = __name__ + ".apsw.resultsdatabase"

# unqlite interface module name
_UNQLITERESULTS = __name__ + ".unqlite.resultsdatabase"

# vedis interface module name
_VEDISRESULTS = __name__ + ".vedis.resultsdatabase"

# tkinter Tcl API interface module name
_DB_TCLRESULTS = __name__ + ".db_tkinter.resultsdatabase"

# lmdb interface module name
_LMDBRESULTS = __name__ + ".lmdb.resultsdatabase"

# Map database module names to application module
APPLICATION_DATABASE_MODULE = {
    BERKELEYDB_MODULE: _BERKELEYDBRESULTS,
    BSDDB3_MODULE: _DBRESULTS,
    SQLITE3_MODULE: _SQLITE3RESULTS,
    APSW_MODULE: _APSWRESULTS,
    DPT_MODULE: _DPTRESULTS,
    UNQLITE_MODULE: _UNQLITERESULTS,
    VEDIS_MODULE: _VEDISRESULTS,
    DB_TCL_MODULE: _DB_TCLRESULTS,
    LMDB_MODULE: _LMDBRESULTS,
}

# Default ECF reference data import module name
_BASECORE_ECF_DATA_IMPORT = "..basecore.ecfdataimport"

# Default ECF Online Grading Database data import module name
_BASECORE_ECF_OGD_DATA_IMPORT = "..basecore.ecfogddataimport"

# Map database module names to ECF reference data import module
ECF_DATA_IMPORT_MODULE = {
    BERKELEYDB_MODULE: _BASECORE_ECF_DATA_IMPORT,
    BSDDB3_MODULE: _BASECORE_ECF_DATA_IMPORT,
    SQLITE3_MODULE: _BASECORE_ECF_DATA_IMPORT,
    APSW_MODULE: _BASECORE_ECF_DATA_IMPORT,
    DPT_MODULE: _BASECORE_ECF_DATA_IMPORT,
    UNQLITE_MODULE: _BASECORE_ECF_DATA_IMPORT,
    VEDIS_MODULE: _BASECORE_ECF_DATA_IMPORT,
    DB_TCL_MODULE: _BASECORE_ECF_DATA_IMPORT,
    LMDB_MODULE: _BASECORE_ECF_DATA_IMPORT,
}

# Map database module names to ECF Online Grading Database data import module
ECF_OGD_DATA_IMPORT_MODULE = {
    BERKELEYDB_MODULE: _BASECORE_ECF_OGD_DATA_IMPORT,
    BSDDB3_MODULE: _BASECORE_ECF_OGD_DATA_IMPORT,
    SQLITE3_MODULE: _BASECORE_ECF_OGD_DATA_IMPORT,
    APSW_MODULE: _BASECORE_ECF_OGD_DATA_IMPORT,
    DPT_MODULE: _BASECORE_ECF_OGD_DATA_IMPORT,
    UNQLITE_MODULE: _BASECORE_ECF_OGD_DATA_IMPORT,
    VEDIS_MODULE: _BASECORE_ECF_OGD_DATA_IMPORT,
    DB_TCL_MODULE: _BASECORE_ECF_OGD_DATA_IMPORT,
    LMDB_MODULE: _BASECORE_ECF_OGD_DATA_IMPORT,
}

# Default known name datasource module name
_BASECORE_KNOWN_NAME = "..basecore.knownnamesds"

# Map database module names to known name datasource module name
KNOWN_NAME_DATASOURCE_MODULE = {
    BERKELEYDB_MODULE: _BASECORE_KNOWN_NAME,
    BSDDB3_MODULE: _BASECORE_KNOWN_NAME,
    SQLITE3_MODULE: _BASECORE_KNOWN_NAME,
    APSW_MODULE: _BASECORE_KNOWN_NAME,
    DPT_MODULE: _BASECORE_KNOWN_NAME,
    UNQLITE_MODULE: _BASECORE_KNOWN_NAME,
    VEDIS_MODULE: _BASECORE_KNOWN_NAME,
    DB_TCL_MODULE: _BASECORE_KNOWN_NAME,
    LMDB_MODULE: _BASECORE_KNOWN_NAME,
}

APPLICATION_NAME = "Results"
ERROR_LOG = "ErrorLog"
