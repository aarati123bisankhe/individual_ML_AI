import 'package:flutter/material.dart';

import '../../../../core/theme/app_theme.dart';
import '../../../../core/widgets/info_banner.dart';
import '../../../../core/widgets/section_card.dart';
import '../../data/repositories/navigation_repository_impl.dart';
import '../../domain/entities/navigation_result.dart';

class NavigationPage extends StatefulWidget {
  const NavigationPage({super.key});

  @override
  State<NavigationPage> createState() => _NavigationPageState();
}

class _NavigationPageState extends State<NavigationPage> {
  final TextEditingController _searchController = TextEditingController(
    text: 'milk',
  );
  final NavigationRepositoryImpl _repository = NavigationRepositoryImpl();

  bool _isLoading = false;
  String? _error;
  List<NavigationResult> _results = const [];

  @override
  void initState() {
    super.initState();
    _searchProducts();
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  Future<void> _searchProducts() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final results = await _repository.searchProducts(
        query: _searchController.text.trim(),
        storeId: 'S01',
      );
      setState(() {
        _results = results;
      });
    } catch (_) {
      setState(() {
        _error = 'Unable to load product navigation right now.';
      });
    } finally {
      if (mounted) {
        setState(() {
          _isLoading = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.all(20),
      children: [
        _HeroPanel(
          searchController: _searchController,
          onSearch: _searchProducts,
        ),
        const SizedBox(height: 20),
        const InfoBanner(
          title: 'Navigation AI',
          subtitle:
              'This module is connected to the backend search model and product location dataset.',
          icon: Icons.route_outlined,
          color: AppTheme.primary,
        ),
        const SizedBox(height: 16),
        SectionCard(
          title: 'Search product',
          subtitle: 'Try milk, rice, momo, noodles, soap, or juice.',
          icon: Icons.search_rounded,
          accent: AppTheme.primary,
          child: Column(
            children: [
              Row(
                children: [
                  Expanded(
                    child: TextField(
                      controller: _searchController,
                      decoration: const InputDecoration(
                        hintText: 'Search grocery item',
                        prefixIcon: Icon(Icons.shopping_bag_outlined),
                      ),
                      onSubmitted: (_) => _searchProducts(),
                    ),
                  ),
                  const SizedBox(width: 12),
                  FilledButton.icon(
                    onPressed: _isLoading ? null : _searchProducts,
                    icon: const Icon(Icons.travel_explore_rounded),
                    label: const Text('Search'),
                  ),
                ],
              ),
              const SizedBox(height: 16),
              if (_error != null)
                _StateMessage(message: _error!, color: const Color(0xFFB42318))
              else if (_isLoading)
                const LinearProgressIndicator()
              else
                Column(
                  children: _results
                      .map((result) => _NavigationResultTile(result: result))
                      .toList(),
                ),
            ],
          ),
        ),
      ],
    );
  }
}

class _NavigationResultTile extends StatelessWidget {
  const _NavigationResultTile({required this.result});

  final NavigationResult result;

  @override
  Widget build(BuildContext context) {
    final score = result.score * 100;
    return Container(
      margin: const EdgeInsets.only(top: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: const Color(0xFFDCE5DF)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                width: 42,
                height: 42,
                decoration: BoxDecoration(
                  color: AppTheme.primary.withValues(alpha: 0.12),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: const Icon(
                  Icons.place_outlined,
                  color: AppTheme.primary,
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Text(
                  result.productName,
                  style: Theme.of(context).textTheme.titleMedium,
                ),
              ),
            ],
          ),
          Text(
            result.subcategory,
            style: Theme.of(context).textTheme.bodyMedium,
          ),
          const SizedBox(height: 12),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: [
              _ResultChip(label: 'Aisle ${result.aisleId}'),
              _ResultChip(label: 'Shelf ${result.shelfNumber}'),
              _ResultChip(label: 'Zone ${result.zoneId}'),
              _ResultChip(label: 'Rs ${result.priceNpr}'),
              _ResultChip(label: '${score.toStringAsFixed(1)}% match'),
            ],
          ),
        ],
      ),
    );
  }
}

class _ResultChip extends StatelessWidget {
  const _ResultChip({required this.label});

  final String label;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 9),
      decoration: BoxDecoration(
        color: const Color(0xFFF4F8F5),
        borderRadius: BorderRadius.circular(999),
        border: Border.all(color: const Color(0xFFD8E2DD)),
      ),
      child: Text(label, style: Theme.of(context).textTheme.bodyMedium),
    );
  }
}

class _HeroPanel extends StatelessWidget {
  const _HeroPanel({required this.searchController, required this.onSearch});

  final TextEditingController searchController;
  final VoidCallback onSearch;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(22),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          colors: [Color(0xFF14532D), Color(0xFF0F766E)],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(24),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Find products faster inside the store',
            style: TextStyle(
              fontSize: 28,
              fontWeight: FontWeight.w700,
              color: Colors.white,
            ),
          ),
          const SizedBox(height: 10),
          const Text(
            'Customers can search for any item and the app returns aisle, shelf, and zone guidance in seconds.',
            style: TextStyle(
              fontSize: 14,
              color: Color(0xFFE8F4EE),
              height: 1.45,
            ),
          ),
          const SizedBox(height: 18),
          Container(
            padding: const EdgeInsets.all(10),
            decoration: BoxDecoration(
              color: Colors.white.withValues(alpha: 0.12),
              borderRadius: BorderRadius.circular(18),
            ),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: searchController,
                    decoration: const InputDecoration(
                      hintText: 'Search milk, rice, momo, soap...',
                      prefixIcon: Icon(Icons.search_rounded),
                      fillColor: Colors.white,
                    ),
                    onSubmitted: (_) => onSearch(),
                  ),
                ),
                const SizedBox(width: 10),
                FilledButton.icon(
                  onPressed: onSearch,
                  style: FilledButton.styleFrom(
                    backgroundColor: Colors.white,
                    foregroundColor: AppTheme.primary,
                  ),
                  icon: const Icon(Icons.travel_explore_rounded),
                  label: const Text('Find'),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _StateMessage extends StatelessWidget {
  const _StateMessage({required this.message, required this.color});

  final String message;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Text(
      message,
      style: TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: color),
    );
  }
}
