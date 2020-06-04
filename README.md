# UPB Bendungan using Flask

- Testing using command 'source .env \\ flask shell testr.py'
- comment column 'content' for table Raw for testing, because the test use sqlite3
- using db.create_all() because single table creation call upb_app init file which call the config.py file, resetting config 'SQLALCHEMY_DATABASE_URI' into postgres setting
