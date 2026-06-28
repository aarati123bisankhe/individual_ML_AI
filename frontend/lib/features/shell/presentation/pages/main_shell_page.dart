import 'package:flutter/material.dart';

import '../../../dashboard/presentation/pages/dashboard_page.dart';
import '../../../inventory/presentation/pages/inventory_page.dart';
import '../../../navigation/presentation/pages/navigation_page.dart';
import '../../../scan_to_pay/presentation/pages/scan_to_pay_page.dart';

class MainShellPage extends StatefulWidget {
  const MainShellPage({super.key});

  @override
  State<MainShellPage> createState() => _MainShellPageState();
}

class _MainShellPageState extends State<MainShellPage> {
  int _currentIndex = 0;

  static const List<Widget> _pages = [
    NavigationPage(),
    ScanToPayPage(),
    InventoryPage(),
    DashboardPage(),
  ];

  static const List<String> _titles = [
    'Navigation',
    'Scan-to-Pay',
    'Inventory',
    'Dashboard',
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(_titles[_currentIndex]),
      ),
      body: IndexedStack(
        index: _currentIndex,
        children: _pages,
      ),
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _currentIndex,
        onTap: (index) {
          setState(() {
            _currentIndex = index;
          });
        },
        items: const [
          BottomNavigationBarItem(
            icon: Icon(Icons.route_outlined),
            activeIcon: Icon(Icons.route_rounded),
            label: 'Navigate',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.qr_code_scanner_outlined),
            activeIcon: Icon(Icons.qr_code_scanner_rounded),
            label: 'Scan',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.inventory_2_outlined),
            activeIcon: Icon(Icons.inventory_2_rounded),
            label: 'Inventory',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.analytics_outlined),
            activeIcon: Icon(Icons.analytics_rounded),
            label: 'Dashboard',
          ),
        ],
      ),
    );
  }
}
