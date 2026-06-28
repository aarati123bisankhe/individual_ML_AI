import '../entities/scan_product.dart';

abstract class ScanToPayRepository {
  Future<List<ScanProduct>> getDemoProducts();
}
