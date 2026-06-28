import '../../domain/entities/dashboard_summary.dart';
import '../../domain/repositories/dashboard_repository.dart';
import '../datasources/dashboard_remote_data_source.dart';

class DashboardRepositoryImpl implements DashboardRepository {
  DashboardRepositoryImpl({DashboardRemoteDataSource? remoteDataSource})
      : _remoteDataSource = remoteDataSource ?? DashboardRemoteDataSource();

  final DashboardRemoteDataSource _remoteDataSource;

  @override
  Future<DashboardSummary> getSummary() {
    return _remoteDataSource.getSummary();
  }
}
