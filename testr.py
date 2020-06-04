import os
import unittest

from flask import request, Response, url_for
from config import basedir
from upb_app import app, db
from upb_app.models import Users, Embung, Bendungan


class TestCase(unittest.TestCase):
    get_urls_public = [
        '/bendungan/kegiatan',
        '/bendungan/petugas',
        '/profile/struktur-organisasi',
        '/profile/wilayah-kerja',
        '/profile/kontak-kami',
        '/map/bendungan',
        '/map/embung',
        '/bendungan',
        '/embung',
        '/login',
        '/logout',
        '/',
        '/intentional/error'
    ]
    get_urls_admin = [
        '/admin/bendungan/operasi/harian',
        '/admin/bendungan/keamanan',
        '/admin/bendungan/kegiatan',
        '/admin/bendungan/kinerja',
        '/admin/bendungan/operasi',
        '/admin/bendungan/petugas',
        '/admin/bendungan/rtow',
        '/admin/embung/harian',
        '/admin/embung/kegiatan',
        '/admin/bendungan',
        '/admin/embung',
        '/admin/users'
    ]

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

    def test_get_urls_public_status(self):
        print("### Testing URL with GET methods ###")
        for url in self.get_urls_public:
            with app.test_request_context(url):
                resp = self.app.get(url)
                if resp.status != '200 OK':
                    print(f"-Error : GET METHOD request for {url} returns {resp.status} code")

    def test_public_api(self):
        print("### Testing Public API ###")
        for url in self.public_api_urls:
            with app.test_request_context(url):
                resp = self.app.get(url)
                if resp.status != '200 OK':
                    print(f"-Error : GET METHOD request for {url} returns {resp.status} code")

    def not_a_test(self):
        print("not a test")


if __name__ == '__main__':
    unittest.main()
