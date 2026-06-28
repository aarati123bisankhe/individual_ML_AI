import '../../../../core/api/api_endpoints.dart';
import '../../../../core/network/api_client.dart';
import '../models/navigation_result_model.dart';

class NavigationRemoteDataSource {
  NavigationRemoteDataSource({ApiClient? client})
      : _client = client ?? const ApiClient();

  final ApiClient _client;

  Future<List<NavigationResultModel>> searchProducts({
    required String query,
    required String storeId,
    int topK = 5,
  }) async {
    final uri = Uri.parse(
      '${ApiEndpoints.navigationSearch}?q=${Uri.encodeQueryComponent(query)}&store_id=$storeId&top_k=$topK',
    );
    final response = await _client.getMap(uri);
    final results = response['results'] as List<dynamic>? ?? const [];
    return results
        .map((item) => NavigationResultModel.fromJson(item as Map<String, dynamic>))
        .toList();
  }
}
