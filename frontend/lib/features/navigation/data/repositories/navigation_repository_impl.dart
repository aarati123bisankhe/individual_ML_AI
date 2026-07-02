import '../../domain/entities/navigation_result.dart';
import '../../domain/repositories/navigation_repository.dart';
import '../datasources/navigation_remote_data_source.dart';

class NavigationRepositoryImpl implements NavigationRepository {
  NavigationRepositoryImpl({NavigationRemoteDataSource? remoteDataSource})
    : _remoteDataSource = remoteDataSource ?? NavigationRemoteDataSource();

  final NavigationRemoteDataSource _remoteDataSource;

  @override
  Future<List<NavigationResult>> searchProducts({
    required String query,
    required String storeId,
    int topK = 5,
  }) {
    return _remoteDataSource.searchProducts(
      query: query,
      storeId: storeId,
      topK: topK,
    );
  }
}
