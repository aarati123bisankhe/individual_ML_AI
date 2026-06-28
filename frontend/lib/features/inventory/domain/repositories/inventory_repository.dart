import '../entities/demand_forecast.dart';

abstract class InventoryRepository {
  Future<List<DemandForecast>> getDemandForecast({
    required String productId,
    required String storeId,
  });
}
