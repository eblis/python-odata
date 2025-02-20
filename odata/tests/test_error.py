# -*- coding: utf-8 -*-

import unittest
import json

import requests
import responses

from odata.exceptions import ODataError
from odata.tests import Service, Product


class TestODataError(unittest.TestCase):

    def test_parse_error_json(self):
        expected_code = '0451'
        expected_message = 'Testing error message handling'
        expected_innererror_message = 'Detailed messages here'

        # Initial data ########################################################
        def request_callback(request):
            resp_body = {'error': {
                'code': expected_code,
                'message': expected_message,
                'innererror': {
                    'message': expected_innererror_message
                }
            }}
            headers = {
                'Content-Type': 'application/json;odata.metadata=minimal'
            }
            return requests.codes.bad_request, headers, json.dumps(resp_body)

        with responses.RequestsMock() as rsps:
            rsps.add_callback(
                rsps.GET, Product.__odata_url__(),
                callback=request_callback,
                content_type='application/json',
            )

            def action():
                try:
                    Service.query(Product).first()
                except ODataError as e:
                    errmsg = str(e)
                    assert expected_code in errmsg, 'Code not in text'
                    assert expected_message in errmsg, 'Upper level message not in text'
                    assert expected_innererror_message in errmsg, 'Detailed message not in text'
                    raise

            self.assertRaises(ODataError, action)


    def test_parse_error_json_with_detail(self):
        expected_code = '3000'
        expected_detail_code = '3008'
        expected_message = 'Error creating entity'
        detail_message = 'TEST name already exists'
        expected_detail_message = f'({expected_detail_code}): {detail_message}'

        # Initial data ########################################################
        def request_callback(request):
            resp_body = {'error': {
                'code': expected_code,
                'message': expected_message,
                'details': [
                    {
                        'code': expected_detail_code,
                        'message': detail_message
                    }
                ]
            }}
            headers = {
                'Content-Type': 'application/json;odata.metadata=minimal'
            }
            return requests.codes.bad_request, headers, json.dumps(resp_body)

        with responses.RequestsMock() as rsps:
            rsps.add_callback(
                rsps.GET, Product.__odata_url__(),
                callback=request_callback,
                content_type='application/json',
            )

            def action():
                try:
                    Service.query(Product).first()
                except ODataError as e:
                    assert e.code == expected_code
                    assert e.message == expected_message
                    assert e.detailed_message == expected_detail_message
                    raise

            self.assertRaises(ODataError, action)
