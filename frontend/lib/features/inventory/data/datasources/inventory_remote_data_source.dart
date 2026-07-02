import '../../../../core/api/api_endpoints.dart';
import '../../../../core/network/api_client.dart';
import '../models/demand_forecast_model.dart';

class InventoryRemoteDataSource {
  InventoryRemoteDataSource({ApiClient? client})
    : _client = client ?? const ApiClient();

  final ApiClient _client;

  Future<List<DemandForecastModel>> getDemandForecast({
    required String productId,
    required String storeId,
  }) async {
    final uri = Uri.parse(
      '${ApiEndpoints.inventoryDemand}?product_id=${Uri.encodeQueryComponent(productId)}&store_id=$storeId',
    );
    final response = await _client.getMap(uri);
    final results = response['results'] as List<dynamic>? ?? const [];
    return results
        .take(5)
        .map(
          (item) => DemandForecastModel.fromJson(item as Map<String, dynamic>),
        )
        .toList();
  }
}
