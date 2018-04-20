# -*- coding: utf-8 -*-
import unittest
import time
from datetime import datetime, timedelta

from openprocurement_client.resources.assets import AssetsClient
from openprocurement_client.resources.lots import LotsClient
from openprocurement_client.clients import APIResourceClient

from openregistry.lots.loki.tests.json_data import (
    test_loki_lot_data
)
from openregistry.assets.bounce.tests.json_data import (
    test_asset_bounce_data
)

# Config with info about API
# config = {
#     "url": "https://lb.api-sandbox.registry.ea.openprocurement.net",
#     "version": 0,
#     "token": "",
#     "auction_url": "https://lb.api-sandbox.ea.openprocurement.org",
#     "auction_token": "",
#     "auction_version": 2.5
# }
config = {
    "url": "http://127.0.0.1:6543",
    "version": 2.4,
    "token": "broker",
}

test_asset_bounce_data['assetHolder'] = {
    'name': 'Just assetHolder',
    'identifier': {
        'scheme': 'UA-EDR',
        'legalName': 'Just a legal name',
        'id': '11111-4',
        'uri': 'https://127.0.0.1:8000'
    }
}
# Data for test
test_asset_bounce_data['mode'] = 'test'
test_loki_lot_data['mode'] = 'test'


class InternalTest(unittest.TestCase):
    '''
        Internal TestCase for openregistry correctness.
        openprocurement.client.python for request

        Test workflow, concierge(bot), convoy(bot) and
        check switching statuses
    '''

    def setUp(self):
        # Init client for 2 resources
        self.lots_client = LotsClient(
            key=config['token'],
            host_url=config['url'],
            api_version=config['version']
        )
        self.assets_client = AssetsClient(
            key=config['token'],
            host_url=config['url'],
            api_version=config['version']
        )
        # self.auctions_client = APIResourceClient(
        #     resource="auctions",
        #     key=config['auction_token'],
        #     host_url=config['auction_url'],
        #     api_version=config['auction_version']
        # )

    def ensure_resource_status(self, get_resource, id, status, *args, **kwargs):
        '''
            Wait for switching resource's status
        '''

        times = kwargs.get("times", 20)
        waiting_message = kwargs.get("waiting_message",
                                     "Waiting for resource's ({}) '{}' status".format(id, status))

        for i in reversed(range(times)):
            time.sleep(i)

            resource = get_resource(id).data
            if resource.status == status:
                break
            else:
                print waiting_message

        resource = get_resource(id).data
        self.assertEqual(resource.status, status)

        return resource

    def test_01_general_workflow(self):
        '''
            Create one bounce assets and move them to pending status
            Create lot with this asset and move to composing status
            Wait for concierge move data from asset to lot
        '''

        # Create assets =======================================================
        asset = self.assets_client.create_resource_item({
            "data": test_asset_bounce_data
        })
        asset_id = asset.data.id
        self.assertEqual(asset.data.status, 'draft')

        print "Successfully created assets {}".format(asset.data.id)

        # Move assets to pending ==============================================
        self.assets_client.patch_asset(asset.data.id, {"data": {"status": "pending"}}, asset.access.token)
        self.assertEqual(self.assets_client.get_asset(asset.data.id).data.status,
                         "pending")

        print "Moved assets to 'pending' status"

        # Create lot ==========================================================
        test_loki_lot_data['assets'] = [asset.data.id]
        lot = self.lots_client.create_resource_item({
            "data": test_loki_lot_data
        })
        lot_id = lot.data.id
        self.assertEqual(lot.data.status, 'draft')

        print "Successfully created lot [{}]".format(lot.data.id)

        # Move lot to Pending =================================================
        self.lots_client.patch_lot(lot.data.id, {"data": {"status": "composing"}}, lot.access.token)
        self.assertEqual(self.lots_client.get_lot(lot.data.id).data.status, "composing")

        print "Moved lot to 'composing' status"


        # Check lot and assets statuses =======================================
        upd_lot = self.ensure_resource_status(
            self.lots_client.get_lot,
            lot.data.id, "pending",
            waiting_message="Waiting for Concierge ..."
        )
        for asset in upd_lot.assets:
            upd_asset = self.assets_client.get_asset(asset).data
            self.assertEqual(upd_asset.status, "active")
            self.assertEqual(upd_asset.relatedLot, upd_lot.id)


        lot = self.lots_client.get_lot(lot_id)
        asset = self.assets_client.get_asset(asset_id)
        self.assertEqual(lot.data.get('lotHolder'), asset.data.get('assetHolder'))
        self.assertEqual(lot.data.lotCustodian, asset.data.assetCustodian)
        self.assertEqual(lot.data.decisions[0], test_loki_lot_data['decisions'][0])
        self.assertEqual(lot.data.decisions[1], asset.data.decisions[0])
        self.assertEqual(lot.data.title, asset.data.title)
        self.assertEqual(lot.data.description, asset.data.description)

        print "Concierge has moved lot to 'pending' and assets to 'active' statuses"


if __name__ == '__main__':
    unittest.main()
