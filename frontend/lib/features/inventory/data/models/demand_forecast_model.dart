import '../../domain/entities/demand_forecast.dart';

class DemandForecastModel extends DemandForecast {
  const DemandForecastModel({
    required super.salesDate,
    required super.predictedProbability,
    required super.predictedClass,
  });

  factory DemandForecastModel.fromJson(Map<String, dynamic> json) {
    return DemandForecastModel(
      salesDate: json['sales_date'] as String? ?? '',
      predictedProbability:
          (json['predicted_probability'] as num?)?.toDouble() ?? 0,
      predictedClass: (json['predicted_class'] as num?)?.toInt() ?? 0,
    );
  }
}
