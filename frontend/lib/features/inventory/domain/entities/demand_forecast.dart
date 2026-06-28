class DemandForecast {
  const DemandForecast({
    required this.salesDate,
    required this.predictedProbability,
    required this.predictedClass,
  });

  final String salesDate;
  final double predictedProbability;
  final int predictedClass;
}
