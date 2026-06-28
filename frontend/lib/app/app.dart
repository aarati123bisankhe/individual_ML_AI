import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

import '../core/api/api_endpoints.dart';

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

class SmartRetailHomePage extends StatefulWidget {
  const SmartRetailHomePage({super.key});

  @override
  State<SmartRetailHomePage> createState() => _SmartRetailHomePageState();
}

class _SmartRetailHomePageState extends State<SmartRetailHomePage> {
  final TextEditingController _searchController = TextEditingController(
    text: 'milk',
  );
  final TextEditingController _productIdController = TextEditingController(
    text: 'P000001',
  );

  List<dynamic> _searchResults = const [];
  Map<String, dynamic>? _dashboardSummary;
  List<dynamic> _demandResults = const [];
  bool _isSearching = false;
  bool _isLoadingDashboard = false;
  bool _isLoadingDemand = false;
  String? _searchError;
  String? _dashboardError;
  String? _demandError;

  @override
  void initState() {
    super.initState();
    _loadInitialData();
  }

  @override
  void dispose() {
    _searchController.dispose();
    _productIdController.dispose();
    super.dispose();
  }

  Future<void> _loadInitialData() async {
    await Future.wait([
      _runSearch(),
      _loadDashboard(),
      _loadDemand(),
    ]);
  }

  Future<void> _runSearch() async {
    setState(() {
      _isSearching = true;
      _searchError = null;
    });

    try {
      final uri = Uri.parse(
        '${ApiEndpoints.navigationSearch}?q=${Uri.encodeQueryComponent(_searchController.text.trim())}&store_id=S01&top_k=5',
      );
      final response = await http.get(uri);
      if (response.statusCode != 200) {
        throw Exception('Navigation search failed');
      }
      final decoded = jsonDecode(response.body) as Map<String, dynamic>;
      setState(() {
        _searchResults = (decoded['results'] as List<dynamic>? ?? const []);
      });
    } catch (_) {
      setState(() {
        _searchError = 'Unable to load product navigation right now.';
      });
    } finally {
      if (mounted) {
        setState(() {
          _isSearching = false;
        });
      }
    }
  }

  Future<void> _loadDashboard() async {
    setState(() {
      _isLoadingDashboard = true;
      _dashboardError = null;
    });

    try {
      final response = await http.get(Uri.parse(ApiEndpoints.dashboardSummary));
      if (response.statusCode != 200) {
        throw Exception('Dashboard summary failed');
      }
      setState(() {
        _dashboardSummary = jsonDecode(response.body) as Map<String, dynamic>;
      });
    } catch (_) {
      setState(() {
        _dashboardError = 'Unable to load AI summary right now.';
      });
    } finally {
      if (mounted) {
        setState(() {
          _isLoadingDashboard = false;
        });
      }
    }
  }

  Future<void> _loadDemand() async {
    setState(() {
      _isLoadingDemand = true;
      _demandError = null;
    });

    try {
      final uri = Uri.parse(
        '${ApiEndpoints.inventoryDemand}?product_id=${Uri.encodeQueryComponent(_productIdController.text.trim())}&store_id=S01',
      );
      final response = await http.get(uri);
      if (response.statusCode != 200) {
        throw Exception('Demand lookup failed');
      }
      final decoded = jsonDecode(response.body) as Map<String, dynamic>;
      setState(() {
        _demandResults = (decoded['results'] as List<dynamic>? ?? const []).take(5).toList();
      });
    } catch (_) {
      setState(() {
        _demandError = 'Unable to load demand forecast right now.';
      });
    } finally {
      if (mounted) {
        setState(() {
          _isLoadingDemand = false;
        });
      }
    }
  }

  Future<void> _refreshAll() async {
    await Future.wait([
      _runSearch(),
      _loadDashboard(),
      _loadDemand(),
    ]);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Smart Grocery'),
        backgroundColor: const Color(0xFFF3F7F4),
        actions: [
          IconButton(
            tooltip: 'Refresh',
            onPressed: _refreshAll,
            icon: const Icon(Icons.refresh_rounded),
          ),
        ],
      ),
      body: SafeArea(
        child: RefreshIndicator(
          onRefresh: _refreshAll,
          child: ListView(
            padding: const EdgeInsets.all(20),
            children: [
              const Text(
                'Retail intelligence for product search, scan-to-pay, and store operations',
                style: TextStyle(
                  fontSize: 28,
                  fontWeight: FontWeight.w700,
                  color: Color(0xFF1B2C24),
                ),
              ),
              const SizedBox(height: 10),
              const Text(
                'This mobile demo connects the customer journey with the AI backend so you can present search, navigation, forecasting, and risk monitoring in one flow.',
                style: TextStyle(
                  fontSize: 15,
                  color: Color(0xFF52635A),
                  height: 1.4,
                ),
              ),
              const SizedBox(height: 24),
              _SectionCard(
                title: 'Product Search and Navigation',
                subtitle: 'Search a grocery item and show aisle, shelf, and zone guidance.',
                icon: Icons.route_outlined,
                accent: const Color(0xFF1D4D3A),
                child: Column(
                  children: [
                    Row(
                      children: [
                        Expanded(
                          child: TextField(
                            controller: _searchController,
                            decoration: _inputDecoration(
                              'Search product',
                              Icons.search_rounded,
                            ),
                            onSubmitted: (_) => _runSearch(),
                          ),
                        ),
                        const SizedBox(width: 12),
                        FilledButton.icon(
                          onPressed: _isSearching ? null : _runSearch,
                          icon: const Icon(Icons.travel_explore_rounded),
                          label: const Text('Find'),
                        ),
                      ],
                    ),
                    const SizedBox(height: 16),
                    if (_searchError != null)
                      _ErrorText(message: _searchError!)
                    else if (_isSearching)
                      const LinearProgressIndicator()
                    else if (_searchResults.isEmpty)
                      const _EmptyState(message: 'No matching products found.')
                    else
                      Column(
                        children: _searchResults
                            .map((item) => _NavigationResultCard(
                                  result: item as Map<String, dynamic>,
                                ))
                            .toList(),
                      ),
                  ],
                ),
              ),
              const SizedBox(height: 16),
              _SectionCard(
                title: 'AI Performance Summary',
                subtitle: 'Live model accuracy scores from the project outputs.',
                icon: Icons.analytics_outlined,
                accent: const Color(0xFF7349A0),
                child: _dashboardError != null
                    ? _ErrorText(message: _dashboardError!)
                    : _isLoadingDashboard
                        ? const LinearProgressIndicator()
                        : _DashboardSummary(summary: _dashboardSummary),
              ),
              const SizedBox(height: 16),
              _SectionCard(
                title: 'Inventory Demand Forecast',
                subtitle: 'Check whether a product is likely to need replenishment soon.',
                icon: Icons.inventory_2_outlined,
                accent: const Color(0xFF2E6EA6),
                child: Column(
                  children: [
                    Row(
                      children: [
                        Expanded(
                          child: TextField(
                            controller: _productIdController,
                            decoration: _inputDecoration(
                              'Product ID',
                              Icons.qr_code_2_outlined,
                            ),
                            onSubmitted: (_) => _loadDemand(),
                          ),
                        ),
                        const SizedBox(width: 12),
                        OutlinedButton.icon(
                          onPressed: _isLoadingDemand ? null : _loadDemand,
                          icon: const Icon(Icons.show_chart_rounded),
                          label: const Text('Forecast'),
                        ),
                      ],
                    ),
                    const SizedBox(height: 16),
                    if (_demandError != null)
                      _ErrorText(message: _demandError!)
                    else if (_isLoadingDemand)
                      const LinearProgressIndicator()
                    else if (_demandResults.isEmpty)
                      const _EmptyState(message: 'No demand forecast available.')
                    else
                      Column(
                        children: _demandResults
                            .map((item) => _DemandForecastTile(
                                  result: item as Map<String, dynamic>,
                                ))
                            .toList(),
                      ),
                  ],
                ),
              ),
              const SizedBox(height: 16),
              const _ScanToPayCard(),
            ],
          ),
        ),
      ),
    );
  }

  InputDecoration _inputDecoration(String hint, IconData icon) {
    return InputDecoration(
      hintText: hint,
      prefixIcon: Icon(icon),
      filled: true,
      fillColor: Colors.white,
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(8),
        borderSide: BorderSide.none,
      ),
    );
  }
}

class _SectionCard extends StatelessWidget {
  const _SectionCard({
    required this.title,
    required this.subtitle,
    required this.icon,
    required this.accent,
    required this.child,
  });

  final String title;
  final String subtitle;
  final IconData icon;
  final Color accent;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(8),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                width: 44,
                height: 44,
                decoration: BoxDecoration(
                  color: accent.withValues(alpha: 0.12),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Icon(icon, color: accent),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      title,
                      style: const TextStyle(
                        fontSize: 17,
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
          const SizedBox(height: 16),
          child,
        ],
      ),
    );
  }
}

class _NavigationResultCard extends StatelessWidget {
  const _NavigationResultCard({required this.result});

  final Map<String, dynamic> result;

  @override
  Widget build(BuildContext context) {
    final score = ((result['score'] as num?) ?? 0) * 100;
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: const Color(0xFFF7FAF8),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            '${result['product_name']}',
            style: const TextStyle(
              fontSize: 15,
              fontWeight: FontWeight.w700,
              color: Color(0xFF1B2C24),
            ),
          ),
          const SizedBox(height: 8),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: [
              _InfoChip(label: 'Aisle ${result['aisle_id']}'),
              _InfoChip(label: 'Shelf ${result['shelf_number']}'),
              _InfoChip(label: 'Zone ${result['zone_id']}'),
              _InfoChip(label: 'Rs ${result['price_npr']}'),
              _InfoChip(label: '${score.toStringAsFixed(1)}% match'),
            ],
          ),
        ],
      ),
    );
  }
}

class _DashboardSummary extends StatelessWidget {
  const _DashboardSummary({required this.summary});

  final Map<String, dynamic>? summary;

  @override
  Widget build(BuildContext context) {
    if (summary == null) {
      return const _EmptyState(message: 'No AI summary available.');
    }

    final highDemand =
        (summary!['high_demand_products'] as List<dynamic>? ?? const []);
    final riskyTransactions =
        (summary!['risky_transactions'] as List<dynamic>? ?? const []);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Wrap(
          spacing: 12,
          runSpacing: 12,
          children: [
            _MetricCard(
              title: 'Navigation',
              value: '${summary!['navigation_accuracy_pct']}%',
              color: const Color(0xFF1D4D3A),
            ),
            _MetricCard(
              title: 'Inventory',
              value: '${summary!['inventory_accuracy_pct']}%',
              color: const Color(0xFF2E6EA6),
            ),
            _MetricCard(
              title: 'Scan Risk',
              value: '${summary!['scan_risk_accuracy_pct']}%',
              color: const Color(0xFFD08C60),
            ),
          ],
        ),
        const SizedBox(height: 18),
        const Text(
          'High demand products',
          style: TextStyle(
            fontSize: 15,
            fontWeight: FontWeight.w700,
            color: Color(0xFF1B2C24),
          ),
        ),
        const SizedBox(height: 10),
        if (highDemand.isEmpty)
          const _EmptyState(message: 'No high demand items right now.')
        else
          Column(
            children: highDemand
                .map((item) => _ListRow(
                      title: '${(item as Map<String, dynamic>)['product_id']}',
                      subtitle:
                          'Predicted demand probability ${(item['predicted_probability'] as num).toStringAsFixed(2)} on ${item['sales_date']}',
                    ))
                .toList(),
          ),
        const SizedBox(height: 18),
        const Text(
          'Risky scan-to-pay transactions',
          style: TextStyle(
            fontSize: 15,
            fontWeight: FontWeight.w700,
            color: Color(0xFF1B2C24),
          ),
        ),
        const SizedBox(height: 10),
        if (riskyTransactions.isEmpty)
          const _EmptyState(message: 'No risky transactions flagged.')
        else
          Column(
            children: riskyTransactions
                .map((item) => _ListRow(
                      title:
                          '${(item as Map<String, dynamic>)['transaction_id']}',
                      subtitle:
                          '${item['payment_method']} payment with risk probability ${(item['predicted_probability'] as num).toStringAsFixed(2)}',
                    ))
                .toList(),
          ),
      ],
    );
  }
}

class _DemandForecastTile extends StatelessWidget {
  const _DemandForecastTile({required this.result});

  final Map<String, dynamic> result;

  @override
  Widget build(BuildContext context) {
    final probability = ((result['predicted_probability'] as num?) ?? 0) * 100;
    final demandLabel =
        (result['predicted_class'] as num?) == 1 ? 'Restock likely' : 'Stable';
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: const Color(0xFFF7FAF8),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Row(
        children: [
          Container(
            width: 42,
            height: 42,
            decoration: BoxDecoration(
              color: const Color(0xFF2E6EA6).withValues(alpha: 0.12),
              borderRadius: BorderRadius.circular(8),
            ),
            child: const Icon(
              Icons.trending_up_rounded,
              color: Color(0xFF2E6EA6),
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  '${result['sales_date']}',
                  style: const TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.w700,
                    color: Color(0xFF1B2C24),
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  '$demandLabel • ${probability.toStringAsFixed(1)}% probability',
                  style: const TextStyle(
                    fontSize: 13,
                    color: Color(0xFF5A6B63),
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

class _ScanToPayCard extends StatelessWidget {
  const _ScanToPayCard();

  @override
  Widget build(BuildContext context) {
    return const _SectionCard(
      title: 'Scan-to-Pay Flow',
      subtitle: 'The customer scans products, pays digitally, and updates store inventory instantly.',
      icon: Icons.qr_code_scanner_outlined,
      accent: Color(0xFFD08C60),
      child: Column(
        children: [
          _ListRow(
            title: '1. Scan item',
            subtitle: 'Barcode or QR code adds the product to the in-app cart.',
          ),
          _ListRow(
            title: '2. Review total',
            subtitle: 'The basket updates instantly with quantity and total price.',
          ),
          _ListRow(
            title: '3. Pay in app',
            subtitle: 'eSewa, Khalti, IME Pay, or card can complete checkout.',
          ),
          _ListRow(
            title: '4. Update inventory',
            subtitle: 'Purchased quantity reduces stock and appears in the dashboard.',
          ),
        ],
      ),
    );
  }
}

class _MetricCard extends StatelessWidget {
  const _MetricCard({
    required this.title,
    required this.value,
    required this.color,
  });

  final String title;
  final String value;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 150,
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            title,
            style: TextStyle(
              fontSize: 13,
              fontWeight: FontWeight.w600,
              color: color,
            ),
          ),
          const SizedBox(height: 6),
          Text(
            value,
            style: const TextStyle(
              fontSize: 24,
              fontWeight: FontWeight.w800,
              color: Color(0xFF1B2C24),
            ),
          ),
        ],
      ),
    );
  }
}

class _ListRow extends StatelessWidget {
  const _ListRow({
    required this.title,
    required this.subtitle,
  });

  final String title;
  final String subtitle;

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: const Color(0xFFF7FAF8),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            title,
            style: const TextStyle(
              fontSize: 14,
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
    );
  }
}

class _InfoChip extends StatelessWidget {
  const _InfoChip({required this.label});

  final String label;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: const Color(0xFFD8E2DD)),
      ),
      child: Text(
        label,
        style: const TextStyle(
          fontSize: 12,
          fontWeight: FontWeight.w600,
          color: Color(0xFF46574E),
        ),
      ),
    );
  }
}

class _EmptyState extends StatelessWidget {
  const _EmptyState({required this.message});

  final String message;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFFF7FAF8),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Text(
        message,
        style: const TextStyle(
          fontSize: 13,
          color: Color(0xFF5A6B63),
        ),
      ),
    );
  }
}

class _ErrorText extends StatelessWidget {
  const _ErrorText({required this.message});

  final String message;

  @override
  Widget build(BuildContext context) {
    return Text(
      message,
      style: const TextStyle(
        color: Color(0xFFB42318),
        fontSize: 13,
        fontWeight: FontWeight.w600,
      ),
    );
  }
}
