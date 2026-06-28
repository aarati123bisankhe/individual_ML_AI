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
        Text(
          'Find products faster inside the store',
          style: Theme.of(context).textTheme.headlineMedium,
        ),
        const SizedBox(height: 10),
        Text(
          'Customers can search for any item and the app returns aisle, shelf, and store zone guidance.',
          style: Theme.of(context).textTheme.bodyLarge,
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
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: const Color(0xFFF7FAF8),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            result.productName,
            style: Theme.of(context).textTheme.titleMedium,
          ),
          const SizedBox(height: 8),
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
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: const Color(0xFFD8E2DD)),
      ),
      child: Text(label, style: Theme.of(context).textTheme.bodyMedium),
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
