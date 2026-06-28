class DashboardSummary {
  const DashboardSummary({
    required this.navigationAccuracyPct,
    required this.inventoryAccuracyPct,
    required this.scanRiskAccuracyPct,
    required this.highDemandProducts,
    required this.riskyTransactions,
  });

  final double navigationAccuracyPct;
  final double inventoryAccuracyPct;
  final double scanRiskAccuracyPct;
  final List<Map<String, dynamic>> highDemandProducts;
  final List<Map<String, dynamic>> riskyTransactions;
}
