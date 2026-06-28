import 'package:flutter/material.dart';

void runSmartRetailApp() {
  runApp(const SmartRetailApp());
}

class SmartRetailApp extends StatelessWidget {
  const SmartRetailApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'Smart Grocery',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF1D4D3A),
          primary: const Color(0xFF1D4D3A),
          secondary: const Color(0xFFD08C60),
          surface: const Color(0xFFF7FAF8),
        ),
        scaffoldBackgroundColor: const Color(0xFFF3F7F4),
        useMaterial3: true,
      ),
      home: const SmartRetailHomePage(),
    );
  }
}

class SmartRetailHomePage extends StatelessWidget {
  const SmartRetailHomePage({super.key});

  @override
  Widget build(BuildContext context) {
    final searchController = TextEditingController(text: 'milk');

    return Scaffold(
      appBar: AppBar(
        title: const Text('Smart Grocery'),
        backgroundColor: const Color(0xFFF3F7F4),
      ),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                'Search, navigate, scan, and pay',
                style: TextStyle(
                  fontSize: 28,
                  fontWeight: FontWeight.w700,
                  color: Color(0xFF1B2C24),
                ),
              ),
              const SizedBox(height: 10),
              const Text(
                'A first working frontend shell for product finding, scan-to-pay, and store operations.',
                style: TextStyle(fontSize: 15, color: Color(0xFF52635A), height: 1.4),
              ),
              const SizedBox(height: 24),
              TextField(
                controller: searchController,
                decoration: InputDecoration(
                  hintText: 'Search product',
                  prefixIcon: const Icon(Icons.search),
                  filled: true,
                  fillColor: Colors.white,
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(8),
                    borderSide: BorderSide.none,
                  ),
                ),
              ),
              const SizedBox(height: 18),
              Expanded(
                child: ListView(
                  children: const [
                    _FeatureCard(
                      title: 'Product Search',
                      subtitle: 'Find milk, rice, momo, soap, or any product by name.',
                      icon: Icons.shopping_bag_outlined,
                      color: Color(0xFF1D4D3A),
                    ),
                    SizedBox(height: 12),
                    _FeatureCard(
                      title: 'Store Navigation',
                      subtitle: 'Show aisle, shelf, and section guidance inside the supermarket.',
                      icon: Icons.route_outlined,
                      color: Color(0xFF2E6EA6),
                    ),
                    SizedBox(height: 12),
                    _FeatureCard(
                      title: 'Scan-to-Pay',
                      subtitle: 'Scan products into a digital cart and pay without a cashier queue.',
                      icon: Icons.qr_code_scanner_outlined,
                      color: Color(0xFFD08C60),
                    ),
                    SizedBox(height: 12),
                    _FeatureCard(
                      title: 'Manager Dashboard',
                      subtitle: 'Track stock, demand prediction, best sellers, and scan-risk alerts.',
                      icon: Icons.dashboard_outlined,
                      color: Color(0xFF7349A0),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
      bottomNavigationBar: Container(
        padding: const EdgeInsets.fromLTRB(20, 12, 20, 20),
        color: const Color(0xFFF3F7F4),
        child: Row(
          children: [
            Expanded(
              child: FilledButton.icon(
                onPressed: null,
                icon: const Icon(Icons.play_arrow_rounded),
                label: const Text('Search Demo'),
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: OutlinedButton.icon(
                onPressed: null,
                icon: const Icon(Icons.analytics_outlined),
                label: const Text('Dashboard'),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _FeatureCard extends StatelessWidget {
  const _FeatureCard({
    required this.title,
    required this.subtitle,
    required this.icon,
    required this.color,
  });

  final String title;
  final String subtitle;
  final IconData icon;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(8),
      ),
      child: Row(
        children: [
          Container(
            width: 48,
            height: 48,
            decoration: BoxDecoration(
              color: color.withValues(alpha: 0.14),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Icon(icon, color: color),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: const TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.w700,
                    color: Color(0xFF1B2C24),
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  subtitle,
                  style: const TextStyle(
                    fontSize: 13,
                    color: Color(0xFF5A6B63),
                    height: 1.35,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
