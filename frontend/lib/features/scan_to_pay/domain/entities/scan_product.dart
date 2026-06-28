class ScanProduct {
  const ScanProduct({
    required this.id,
    required this.barcode,
    required this.name,
    required this.category,
    required this.priceNpr,
    required this.aisleId,
  });

  final String id;
  final String barcode;
  final String name;
  final String category;
  final double priceNpr;
  final String aisleId;
}
