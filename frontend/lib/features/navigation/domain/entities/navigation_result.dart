class NavigationResult {
  const NavigationResult({
    required this.productId,
    required this.productName,
    required this.subcategory,
    required this.storeId,
    required this.zoneId,
    required this.aisleId,
    required this.shelfNumber,
    required this.shelfPosition,
    required this.priceNpr,
    required this.score,
  });

  final String productId;
  final String productName;
  final String subcategory;
  final String storeId;
  final String zoneId;
  final String aisleId;
  final int shelfNumber;
  final int shelfPosition;
  final num priceNpr;
  final double score;
}
