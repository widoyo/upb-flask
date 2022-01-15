# UPB Bendungan using Flask

### Testing
- Testing using command :
1. 'source .env \\ flask shell tests/basic_test.py'
2. 'source .env \\ flask shell tests/api_test.py'

- comment column 'content' for table Raw for testing, because the test use sqlite3

- using db.create_all() because single table creation call upb_app init file which call the config.py file, resetting config 'SQLALCHEMY_DATABASE_URI' into postgres setting

### Run using Docker Compose
- run on the background
`sudo docker-compose up -d`
- check services status
`sudo docker-compose ps`
- check logs
`sudo docker-compose logs web`
- open database console
`sudo docker-compose exec db psql -U <dbuser> -d <dbname>`
- stop services
`sudo docker-compose down`
