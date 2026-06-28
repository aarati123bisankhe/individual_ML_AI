import '../../domain/entities/demand_forecast.dart';
import '../../domain/repositories/inventory_repository.dart';
import '../datasources/inventory_remote_data_source.dart';

class InventoryRepositoryImpl implements InventoryRepository {
  InventoryRepositoryImpl({InventoryRemoteDataSource? remoteDataSource})
      : _remoteDataSource = remoteDataSource ?? InventoryRemoteDataSource();

  final InventoryRemoteDataSource _remoteDataSource;

  @override
  Future<List<DemandForecast>> getDemandForecast({
    required String productId,
    required String storeId,
  }) {
    return _remoteDataSource.getDemandForecast(
      productId: productId,
      storeId: storeId,
    );
  }
}
