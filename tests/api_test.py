import os
import unittest

from flask import request, Response, url_for
from config import basedir
from upb_app import app, db
from upb_app.models import Users, Embung, Bendungan


class TestCase(unittest.TestCase):
    public_api_urls = [
        '/api/bendungan/periodic'
    ]

    def setUp(self):
        # column 'content' in Raw table needs to be commented
        # or it will fail the tests
        # creating tables one by one create the tables on postgresql for some reason
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'test.db')
        self.app = app.test_client()
        db.create_all()
        print()

    def tearDown(self):
        # print("### Dropping Test DB ###")
        print()
        db.session.remove()
        db.drop_all()

    def test_public_api(self):
        print("### Testing Public API ###")
        for url in self.public_api_urls:
            print(f"\ntesting url {url}")
            with app.test_request_context(url):
                resp = self.app.get(url)
                if resp.status != '200 OK':
                    print(f"-Error : GET METHOD request for {url} returns {resp.status} code")


if __name__ == '__main__':
    unittest.main()
