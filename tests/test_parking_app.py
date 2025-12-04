"""
Unit Tests for ELC Parking App
Author: Jie Liang
Course: CS2450

Tests the core functionality of ParkingLot, User, and ParkingSystem classes
"""

import unittest
import sys
import os

# Add the parent directory to the path to import the parking app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the classes from your parking app
# Note: Adjust the import based on your actual file structure
try:
    from parking_app_UPDATED import (
        ParkingLot, 
        User, 
        ParkingSystem, 
        UserType, 
        ParkingStatus
    )
except ImportError:
    print("Error: Could not import from parking_app_UPDATED.py")
    print("Make sure this test file is in the same directory as parking_app_UPDATED.py")
    sys.exit(1)


class TestParkingLot(unittest.TestCase):
    """Test cases for ParkingLot class"""
    
    def setUp(self):
        """Set up test fixtures before each test"""
        self.lot = ParkingLot("17", "Lot 17", 35, "Student", 2, 4)
    
    def test_initialization(self):
        """Test that ParkingLot initializes correctly"""
        self.assertEqual(self.lot.lot_id, "17")
        self.assertEqual(self.lot.name, "Lot 17")
        self.assertEqual(self.lot.total_spaces, 35)
        self.assertEqual(self.lot.permit_type, "Student")
    
    def test_availability_calculation(self):
        """Test available spaces calculation"""
        # Initially all spaces should be available
        self.assertEqual(self.lot.available_spaces, 35)
        
        # Update occupancy
        self.lot.update_occupancy(10)
        self.assertEqual(self.lot.available_spaces, 25)
    
    def test_status_full(self):
        """Test status when lot is full"""
        self.lot.update_occupancy(35)
        status = self.lot.get_status()
        self.assertEqual(status, ParkingStatus.FULL)
    
    def test_status_available(self):
        """Test status when lot has plenty of space"""
        self.lot.update_occupancy(10)  # 25/35 available = 71%
        status = self.lot.get_status()
        self.assertEqual(status, ParkingStatus.AVAILABLE)
    
    def test_status_limited(self):
        """Test status when lot has limited space"""
        self.lot.update_occupancy(32)  # 3/35 available = 8.5%
        status = self.lot.get_status()
        self.assertEqual(status, ParkingStatus.LIMITED)
    
    def test_can_user_park_student(self):
        """Test that students can park in student lot"""
        can_park = self.lot.can_user_park(UserType.STUDENT)
        self.assertTrue(can_park)
    
    def test_can_user_park_staff(self):
        """Test that staff cannot park in student lot"""
        can_park = self.lot.can_user_park(UserType.STAFF)
        self.assertFalse(can_park)
    
    def test_occupancy_bounds(self):
        """Test that occupancy stays within valid bounds"""
        # Test upper bound
        self.lot.update_occupancy(100)  # Try to exceed capacity
        self.assertEqual(self.lot.available_spaces, 0)
        
        # Test lower bound
        self.lot.update_occupancy(-10)  # Try negative
        self.assertEqual(self.lot.available_spaces, 35)


class TestUser(unittest.TestCase):
    """Test cases for User class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.user = User("001", "John Doe", UserType.STUDENT)
    
    def test_initialization(self):
        """Test User initialization"""
        self.assertEqual(self.user.name, "John Doe")
        self.assertEqual(self.user.user_type, UserType.STUDENT)
    
    def test_get_permitted_lots(self):
        """Test filtering lots by user permission"""
        lots = [
            ParkingLot("17", "Lot 17", 35, "Student", 2, 4),
            ParkingLot("18", "Lot 18", 45, "Staff", 1, 3),
            ParkingLot("19", "Lot 19", 60, "Both", 2, 5),
            ParkingLot("14", "Lot 14", 50, "Open", 3, 7)
        ]
        
        permitted = self.user.get_permitted_lots(lots)
        
        # Student should access: Student, Both, and Open lots
        self.assertEqual(len(permitted), 3)
        lot_ids = [lot.lot_id for lot in permitted]
        self.assertIn("17", lot_ids)  # Student lot
        self.assertIn("19", lot_ids)  # Both lot
        self.assertIn("14", lot_ids)  # Open lot


class TestParkingSystem(unittest.TestCase):
    """Test cases for ParkingSystem class (Singleton)"""
    
    def test_singleton_pattern(self):
        """Test that ParkingSystem follows Singleton pattern"""
        system1 = ParkingSystem()
        system2 = ParkingSystem()
        
        # Both should be the same instance
        self.assertIs(system1, system2)
    
    def test_get_all_lots(self):
        """Test retrieving all parking lots"""
        system = ParkingSystem()
        lots = system.get_all_lots()
        
        # Should have 4 lots (14, 17, 18, 19)
        self.assertEqual(len(lots), 4)
    
    def test_get_lot_by_id(self):
        """Test retrieving specific lot by ID"""
        system = ParkingSystem()
        lot = system.get_lot_by_id("17")
        
        self.assertIsNotNone(lot)
        self.assertEqual(lot.lot_id, "17")
        self.assertEqual(lot.name, "Lot 17")
    
    def test_get_lot_invalid_id(self):
        """Test retrieving lot with invalid ID"""
        system = ParkingSystem()
        lot = system.get_lot_by_id("999")
        
        self.assertIsNone(lot)


class TestIntegration(unittest.TestCase):
    """Integration tests for the complete system"""
    
    def test_full_workflow(self):
        """Test a complete user workflow"""
        # Create system
        system = ParkingSystem()
        
        # Create user
        user = User("001", "Jane Student", UserType.STUDENT)
        
        # Get available lots for this user
        all_lots = system.get_all_lots()
        permitted_lots = user.get_permitted_lots(all_lots)
        
        # Should have at least 3 lots available for student
        self.assertGreaterEqual(len(permitted_lots), 3)
        
        # Verify lot 18 (Staff) is NOT in permitted lots
        staff_lot_ids = [lot.lot_id for lot in permitted_lots if lot.lot_id == "18"]
        self.assertEqual(len(staff_lot_ids), 0)


def run_tests_with_summary():
    """Run all tests and print a summary"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestParkingLot))
    suite.addTests(loader.loadTestsFromTestCase(TestUser))
    suite.addTests(loader.loadTestsFromTestCase(TestParkingSystem))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Total Tests Run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("="*70)
    
    return result


if __name__ == '__main__':
    print("="*70)
    print("ELC PARKING APP - UNIT TESTS")
    print("="*70)
    print()
    
    result = run_tests_with_summary()
    
    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)
