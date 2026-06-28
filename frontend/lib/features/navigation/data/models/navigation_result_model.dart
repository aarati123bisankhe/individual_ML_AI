import '../../domain/entities/navigation_result.dart';

class NavigationResultModel extends NavigationResult {
  const NavigationResultModel({
    required super.productId,
    required super.productName,
    required super.subcategory,
    required super.storeId,
    required super.zoneId,
    required super.aisleId,
    required super.shelfNumber,
    required super.shelfPosition,
    required super.priceNpr,
    required super.score,
  });

  factory NavigationResultModel.fromJson(Map<String, dynamic> json) {
    return NavigationResultModel(
      productId: json['product_id'] as String,
      productName: json['product_name'] as String,
      subcategory: json['subcategory'] as String? ?? '',
      storeId: json['store_id'] as String? ?? '',
      zoneId: json['zone_id'] as String? ?? '',
      aisleId: json['aisle_id'] as String? ?? '',
      shelfNumber: (json['shelf_number'] as num?)?.toInt() ?? 0,
      shelfPosition: (json['shelf_position'] as num?)?.toInt() ?? 0,
      priceNpr: json['price_npr'] as num? ?? 0,
      score: (json['score'] as num?)?.toDouble() ?? 0,
    );
  }
}
