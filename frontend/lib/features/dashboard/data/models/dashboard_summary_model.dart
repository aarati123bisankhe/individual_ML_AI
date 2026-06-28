import '../../domain/entities/dashboard_summary.dart';

class DashboardSummaryModel extends DashboardSummary {
  const DashboardSummaryModel({
    required super.navigationAccuracyPct,
    required super.inventoryAccuracyPct,
    required super.scanRiskAccuracyPct,
    required super.highDemandProducts,
    required super.riskyTransactions,
  });

  factory DashboardSummaryModel.fromJson(Map<String, dynamic> json) {
    return DashboardSummaryModel(
      navigationAccuracyPct:
          (json['navigation_accuracy_pct'] as num?)?.toDouble() ?? 0,
      inventoryAccuracyPct:
          (json['inventory_accuracy_pct'] as num?)?.toDouble() ?? 0,
      scanRiskAccuracyPct:
          (json['scan_risk_accuracy_pct'] as num?)?.toDouble() ?? 0,
      highDemandProducts: (json['high_demand_products'] as List<dynamic>? ?? const [])
          .cast<Map<String, dynamic>>(),
      riskyTransactions: (json['risky_transactions'] as List<dynamic>? ?? const [])
          .cast<Map<String, dynamic>>(),
    );
  }
}
