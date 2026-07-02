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

  static const List<String> _subtitles = [
    'Find products by aisle and shelf',
    'Scan items and check out faster',
    'Track restock demand signals',
    'Monitor models and store activity',
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        toolbarHeight: 78,
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(_titles[_currentIndex]),
            const SizedBox(height: 2),
            Text(
              _subtitles[_currentIndex],
              style: Theme.of(context).textTheme.bodyMedium,
            ),
          ],
        ),
        actions: [
          Padding(
            padding: const EdgeInsets.only(right: 16),
            child: Container(
              width: 42,
              height: 42,
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(14),
                border: Border.all(color: const Color(0xFFDCE5DF)),
              ),
              child: const Icon(Icons.storefront_outlined, size: 20),
            ),
          ),
        ],
      ),
      body: IndexedStack(index: _currentIndex, children: _pages),
      bottomNavigationBar: Container(
        decoration: const BoxDecoration(
          color: Colors.white,
          border: Border(top: BorderSide(color: Color(0xFFDCE5DF))),
        ),
        child: SafeArea(
          top: false,
          child: BottomNavigationBar(
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
        ),
      ),
    );
  }
}
