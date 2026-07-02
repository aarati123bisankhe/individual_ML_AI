import 'package:flutter/material.dart';

import '../../../../core/theme/app_theme.dart';
import '../../../../core/widgets/metric_tile.dart';
import '../../../../core/widgets/section_card.dart';
import '../../data/repositories/dashboard_repository_impl.dart';
import '../../domain/entities/dashboard_summary.dart';

class DashboardPage extends StatefulWidget {
  const DashboardPage({super.key});

  @override
  State<DashboardPage> createState() => _DashboardPageState();
}

class _DashboardPageState extends State<DashboardPage> {
  final DashboardRepositoryImpl _repository = DashboardRepositoryImpl();

  bool _isLoading = false;
  String? _error;
  DashboardSummary? _summary;

  @override
  void initState() {
    super.initState();
    _loadSummary();
  }

  Future<void> _loadSummary() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final summary = await _repository.getSummary();
      setState(() {
        _summary = summary;
      });
    } catch (_) {
      setState(() {
        _error = 'Unable to load dashboard metrics right now.';
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
        Container(
          padding: const EdgeInsets.all(22),
          decoration: BoxDecoration(
            gradient: const LinearGradient(
              colors: [Color(0xFF7C3AED), Color(0xFF14532D)],
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
            ),
            borderRadius: BorderRadius.circular(24),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: const [
              Text(
                'Store intelligence dashboard',
                style: TextStyle(
                  fontSize: 28,
                  fontWeight: FontWeight.w700,
                  color: Colors.white,
                ),
              ),
              SizedBox(height: 10),
              Text(
                'Managers can monitor model accuracy, forecasted demand, and scan-to-pay risk in one place.',
                style: TextStyle(
                  fontSize: 14,
                  color: Color(0xFFF0ECFF),
                  height: 1.45,
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 20),
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
        else if (_summary != null) ...[
          Wrap(
            spacing: 12,
            runSpacing: 12,
            children: [
              MetricTile(
                title: 'Navigation',
                value: '${_summary!.navigationAccuracyPct.toStringAsFixed(2)}%',
                color: AppTheme.primary,
              ),
              MetricTile(
                title: 'Inventory',
                value: '${_summary!.inventoryAccuracyPct.toStringAsFixed(2)}%',
                color: AppTheme.secondary,
              ),
              MetricTile(
                title: 'Scan Risk',
                value: '${_summary!.scanRiskAccuracyPct.toStringAsFixed(2)}%',
                color: AppTheme.accent,
              ),
            ],
          ),
          const SizedBox(height: 16),
          SectionCard(
            title: 'High demand products',
            subtitle: 'Products with stronger next-day demand probability.',
            icon: Icons.local_shipping_outlined,
            accent: AppTheme.secondary,
            child: Column(
              children: _summary!.highDemandProducts
                  .map(
                    (item) => _DashboardRow(
                      title: '${item['product_id']}',
                      subtitle:
                          'Demand probability ${(((item['predicted_probability'] as num?) ?? 0) * 100).toStringAsFixed(1)}% on ${item['sales_date']}',
                    ),
                  )
                  .toList(),
            ),
          ),
          const SizedBox(height: 16),
          SectionCard(
            title: 'Risky scan-to-pay sessions',
            subtitle: 'Transactions that may need review or extra monitoring.',
            icon: Icons.verified_user_outlined,
            accent: AppTheme.accent,
            child: Column(
              children: _summary!.riskyTransactions
                  .map(
                    (item) => _DashboardRow(
                      title: '${item['transaction_id']}',
                      subtitle:
                          '${item['payment_method']} payment with ${(((item['predicted_probability'] as num?) ?? 0) * 100).toStringAsFixed(1)}% risk score',
                    ),
                  )
                  .toList(),
            ),
          ),
        ],
      ],
    );
  }
}

class _DashboardRow extends StatelessWidget {
  const _DashboardRow({required this.title, required this.subtitle});

  final String title;
  final String subtitle;

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: const Color(0xFFDCE5DF)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(title, style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: 4),
          Text(subtitle, style: Theme.of(context).textTheme.bodyMedium),
        ],
      ),
    );
  }
}
