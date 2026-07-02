import '../../domain/entities/scan_product.dart';
import '../../domain/repositories/scan_to_pay_repository.dart';
import '../datasources/scan_catalog_data_source.dart';

class ScanToPayRepositoryImpl implements ScanToPayRepository {
  ScanToPayRepositoryImpl({ScanCatalogDataSource? dataSource})
    : _dataSource = dataSource ?? ScanCatalogDataSource();

  final ScanCatalogDataSource _dataSource;

  @override
  Future<List<ScanProduct>> getDemoProducts() {
    return _dataSource.getDemoProducts();
  }
}
