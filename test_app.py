import unittest
import json
from app import app, MOCK_TRAIN_DATA
from datetime import datetime

class TestApp(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_mock_data_response(self):
        # Test without keys, should return mock data
        response = self.app.get('/api/data')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('buses', data)
        self.assertIn('trains', data)
        
        # Bus checks
        # Should filter out Arriva (163) and keep First (19, 40)
        lines = [b['line'] for b in data['buses']]
        self.assertNotIn('163', lines)
        self.assertIn('19', lines)
        
        # Train checks
        # Default min_train_time is 30. Mock "now" is 11:45.
        # 12:00 (15m away) -> Filtered
        # 12:05 (20m away) -> Filtered (also CrossCountry)
        # 12:15 (30m away) -> Kept
        # 12:45 (60m away) -> Kept
        # Sorted: 12:15 then 12:45
        times = [t['time'] for t in data['trains']]
        self.assertEqual(times, ['12:15', '12:45'])
        
    def test_train_time_filter(self):
        # Test with min_train_time=10
        # Mock now: 11:45
        # 12:00 (15m) -> Kept
        # 12:05 (CrossCountry) -> Filtered by operator
        # 12:15 -> Kept
        # 12:45 -> Kept
        response = self.app.get('/api/data?min_train_time=10')
        data = json.loads(response.data)
        times = [t['time'] for t in data['trains']]
        # Should include 12:00
        self.assertIn('12:00', times)

    def test_operator_filter(self):
        # Add a CrossCountry train that satisfies the time filter (> 30 mins)
        # to verify it is still filtered out by operator name.
        MOCK_TRAIN_DATA['departures']['all'].append(
            {"destination_name": "Birmingham", "aimed_departure_time": "12:50", "status": "ON TIME", "operator_name": "CrossCountry"}
        )
        
        response = self.app.get('/api/data')
        data = json.loads(response.data)
        destinations = [t['destination'] for t in data['trains']]
        
        # 12:50 is > 30 mins from 11:45 (mock now), so it passes time filter.
        # But it should be filtered by operator.
        self.assertNotIn('Birmingham', destinations)
        
        # Clean up
        MOCK_TRAIN_DATA['departures']['all'].pop()
    
    def test_destination_filter(self):
        # Test bus direction filter
        # Mock data has "East Garforth" and "Seacroft"
        response = self.app.get('/api/data?bus_direction=East')
        data = json.loads(response.data)
        bus_directions = [b['destination'] for b in data['buses']]
        self.assertIn('East Garforth', bus_directions)
        self.assertNotIn('Seacroft', bus_directions)

        # Test train destination filter
        # Mock data has "Cambridge" and "Norwich" (Greater Anglia)
        response = self.app.get('/api/data?train_destination=Norwich')
        data = json.loads(response.data)
        train_destinations = [t['destination'] for t in data['trains']]
        self.assertIn('Norwich', train_destinations)
        self.assertNotIn('Cambridge', train_destinations)
        
if __name__ == '__main__':
    unittest.main()
