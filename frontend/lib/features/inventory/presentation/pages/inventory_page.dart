import 'package:flutter/material.dart';

import '../../../../core/theme/app_theme.dart';
import '../../../../core/widgets/section_card.dart';
import '../../data/repositories/inventory_repository_impl.dart';
import '../../domain/entities/demand_forecast.dart';

class InventoryPage extends StatefulWidget {
  const InventoryPage({super.key});

  @override
  State<InventoryPage> createState() => _InventoryPageState();
}

class _InventoryPageState extends State<InventoryPage> {
  final TextEditingController _productIdController = TextEditingController(
    text: 'P000001',
  );
  final InventoryRepositoryImpl _repository = InventoryRepositoryImpl();

  bool _isLoading = false;
  String? _error;
  List<DemandForecast> _results = const [];

  @override
  void initState() {
    super.initState();
    _loadForecast();
  }

  @override
  void dispose() {
    _productIdController.dispose();
    super.dispose();
  }

  Future<void> _loadForecast() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final results = await _repository.getDemandForecast(
        productId: _productIdController.text.trim(),
        storeId: 'S01',
      );
      setState(() {
        _results = results;
      });
    } catch (_) {
      setState(() {
        _error = 'Unable to load demand forecast right now.';
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
          'Demand forecasting for inventory planning',
          style: Theme.of(context).textTheme.headlineMedium,
        ),
        const SizedBox(height: 10),
        Text(
          'This screen supports the backend inventory system by estimating which products may need replenishment soon.',
          style: Theme.of(context).textTheme.bodyLarge,
        ),
        const SizedBox(height: 20),
        SectionCard(
          title: 'Product forecast',
          subtitle: 'Enter a product ID to review predicted next-day demand.',
          icon: Icons.inventory_2_outlined,
          accent: AppTheme.secondary,
          child: Column(
            children: [
              Row(
                children: [
                  Expanded(
                    child: TextField(
                      controller: _productIdController,
                      decoration: const InputDecoration(
                        hintText: 'Enter product ID',
                        prefixIcon: Icon(Icons.qr_code_2_outlined),
                      ),
                      onSubmitted: (_) => _loadForecast(),
                    ),
                  ),
                  const SizedBox(width: 12),
                  FilledButton.icon(
                    onPressed: _isLoading ? null : _loadForecast,
                    icon: const Icon(Icons.show_chart_rounded),
                    label: const Text('Forecast'),
                  ),
                ],
              ),
              const SizedBox(height: 16),
              if (_error != null)
                Text(
                  _error!,
                  style: const TextStyle(
                    color: Color(0xFFB42318),
                    fontWeight: FontWeight.w600,
                  ),
                )
              else if (_isLoading)
                const LinearProgressIndicator()
              else
                Column(
                  children: _results
                      .map((result) => _ForecastTile(result: result))
                      .toList(),
                ),
            ],
          ),
        ),
      ],
    );
  }
}

class _ForecastTile extends StatelessWidget {
  const _ForecastTile({required this.result});

  final DemandForecast result;

  @override
  Widget build(BuildContext context) {
    final probability = result.predictedProbability * 100;
    final label = result.predictedClass == 1 ? 'Restock likely' : 'Stable';
    return Container(
      margin: const EdgeInsets.only(top: 12),
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
              color: AppTheme.secondary.withValues(alpha: 0.12),
              borderRadius: BorderRadius.circular(8),
            ),
            child: const Icon(Icons.trending_up_rounded, color: AppTheme.secondary),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(result.salesDate, style: Theme.of(context).textTheme.titleMedium),
                const SizedBox(height: 4),
                Text(
                  '$label • ${probability.toStringAsFixed(1)}% probability',
                  style: Theme.of(context).textTheme.bodyMedium,
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
