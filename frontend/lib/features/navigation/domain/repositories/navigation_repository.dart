import '../entities/navigation_result.dart';

abstract class NavigationRepository {
  Future<List<NavigationResult>> searchProducts({
    required String query,
    required String storeId,
    int topK = 5,
  });
}
