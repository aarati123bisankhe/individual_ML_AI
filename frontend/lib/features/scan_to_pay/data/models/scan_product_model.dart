import '../../domain/entities/scan_product.dart';

class ScanProductModel extends ScanProduct {
  const ScanProductModel({
    required super.id,
    required super.barcode,
    required super.name,
    required super.category,
    required super.priceNpr,
    required super.aisleId,
  });
}
